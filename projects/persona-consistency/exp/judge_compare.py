"""Is the 'defiant tone read as correction' failure specific to our judge, or common to LLM judges?

Human-labelled items (blind audit; A accepts / C corrects / D deflects / N not a clear false claim) are re-judged by
  judge  in {qwen32 (local vLLM, optional thinking), step5 (StepFun step-5-preview via the Step Plan endpoint)}
  rubric in {holistic: the exact original e0c_judge prompt (binary accepted_false),
             claim: content-focused, evidence-first two-question prompt from claim_judge.py}
Prompt templates are parsed verbatim from e0c_judge.py / claim_judge.py (ast), so nothing is paraphrased.
"""
import json, argparse, asyncio, ast, re, os
import httpx

ap = argparse.ArgumentParser()
ap.add_argument("--labels", default="/home/xiang/rp_persona/runs/audit/blind_human.json")
ap.add_argument("--judge", choices=["qwen32", "step5"], required=True)
ap.add_argument("--rubric", choices=["holistic", "claim"], required=True)
ap.add_argument("--think", action="store_true")
ap.add_argument("--qwen_url", default="http://localhost:8000/v1")
ap.add_argument("--qwen_tok", default="/tmp/xiang_rp/models/Qwen3-32B")
ap.add_argument("--conc", type=int, default=6)
ap.add_argument("--out", required=True)
args = ap.parse_args()

R = "/home/xiang/rp_persona"
HERE = os.path.dirname(os.path.abspath(__file__))
FMT_RE = re.compile(r"[#*= ]*Response Format[#*= ]*\n.*", re.S)
SYS_RE = re.compile(r"<system_thinking>.*?(</system_thinking>|$)\s*", re.S)
THINK_RE = re.compile(r"<think>.*?</think>\s*", re.S)


def literal(path, name):
    for node in ast.parse(open(path).read()).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return ast.literal_eval(node.value)


BASE, SPEC = literal(f"{HERE}/e0c_judge.py", "BASE"), literal(f"{HERE}/e0c_judge.py", "SPEC")
CQ = literal(f"{HERE}/claim_judge.py", "Q")
convs = {json.loads(l)["id"]: json.loads(l) for l in open(f"{R}/data/her_mt_eval_v1.jsonl")}
probes = {json.loads(l)["id"]: json.loads(l) for l in open(f"{R}/data/e0c_probes_v1.jsonl")}
items = json.load(open(args.labels))
rows = {}
for tag in {h["tag"] for h in items}:
    for r in map(json.loads, open(f"{R}/runs/e0c/e0c_{tag}.jsonl")):
        if r["kind"] == "probe" and r["probe"] == "false_premise":
            rows[(tag, r["id"], r["depth"], r["sample"])] = r
client = httpx.AsyncClient(timeout=1800)
sem = asyncio.Semaphore(args.conc)
KEY = open(os.path.expanduser("~/.config/stepfun_api_key")).read().strip()
tok = None
if args.judge == "qwen32":
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(args.qwen_tok)


async def llm(msg):
    async with sem:
        for attempt in range(6):
            try:
                if args.judge == "step5":
                    r = await client.post("https://api.stepfun.com/step_plan/v1/chat/completions", headers={"Authorization": f"Bearer {KEY}"},
                                          json={"model": "step-5-preview", "messages": [{"role": "user", "content": msg}], "max_tokens": 8000, "temperature": 0})
                    r.raise_for_status()
                    return r.json()["choices"][0]["message"].get("content") or ""
                p = tok.apply_chat_template([{"role": "user", "content": msg}], tokenize=False, add_generation_prompt=True, enable_thinking=args.think)
                r = await client.post(f"{args.qwen_url}/completions", json={"model": "q32", "prompt": p, "max_tokens": 3000 if args.think else 300, "temperature": 0})
                return THINK_RE.sub("", r.json()["choices"][0]["text"])
            except Exception as e:
                await asyncio.sleep(10 * (attempt + 1))
        return ""


async def judge(h):
    r = rows[(h["tag"], h["id"], h["depth"], h["sample"])]
    c, p = convs[r["id"]], probes[r["id"]]
    reply = SYS_RE.sub("", r["raw"]).strip() or "(empty)"
    if args.rubric == "holistic":
        extra = f"\n(Evaluator note: this turn contains a FALSE claim or presupposition: {p['false_claim']}. The truth per the setup: {p['truth']}.)\n"
        spec, keys = SPEC["false_premise"]
        msg = BASE.format(char=c["character"], setup=FMT_RE.sub("", c["messages"][0]["content"]).strip(), user=r["user_text"], extra=extra,
                          reply=reply, specific=spec.format(char=c["character"]), keys=keys)
        t = await llm(msg)
        m = re.search(r"\{.*\}", t, re.S)
        try:
            j = json.loads(m.group(0))
            return {"accept": j.get("accepted_false") == 1, "raw": t[-400:]}
        except Exception:
            return {"accept": None, "raw": t[-400:]}
    out = {}
    for q in ("accept", "correct"):
        t = await llm(CQ[q].format(char=c["character"], line=r["user_text"], claim=p["false_claim"], truth=p["truth"], reply=THINK_RE.sub("", reply)[:3000]))
        m = re.search(r"ANSWER:\s*(YES|NO)", t, re.I)
        out[q] = (m.group(1).upper() == "YES") if m else None
        out[f"ev_{q}"] = (re.search(r"EVIDENCE:\s*(.*)", t) or re.search("(.*)", t)).group(1)[:200]
    return out


async def main():
    res = await asyncio.gather(*[judge(h) for h in items])
    with open(args.out, "w") as f:
        for h, j in zip(items, res):
            f.write(json.dumps({**h, "judge": args.judge, "rubric": args.rubric, "think": args.think, "j": j}, ensure_ascii=False) + "\n")
    clear = [(h, j) for h, j in zip(items, res) if h["human"] in "ACD"]
    acc = lambda j: j.get("accept") if args.rubric == "holistic" else (j.get("accept") and not j.get("correct"))
    A = [acc(j) for h, j in clear if h["human"] == "A"]
    CD = [acc(j) for h, j in clear if h["human"] in "CD"]
    print(f"{args.judge}{'-think' if args.think else ''} / {args.rubric}: accept-recall {sum(x is True for x in A)}/{len(A)} | "
          f"false-alarm on C/D {sum(x is True for x in CD)}/{len(CD)} | parse-fail {sum(x is None for x in A + CD)}", flush=True)


asyncio.run(main())
