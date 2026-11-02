"""Re-judge closed-loop probe replies with StepFun step-5-preview (Step Plan endpoint) using the EXACT original e0c_judge
rubric (prompt templates parsed from e0c_judge.py). On 48 blind human labels this judge caught 12/12 clear acceptances
of false claims (original Qwen3-32B non-thinking judge: 1/12). Output schema matches e0c_judge (.judge_step5.jsonl), so
compare_rounds.py / analysis scripts can read it with --judge_suffix judge_step5. Resumable: already-judged rows are kept.
"""
import json, argparse, asyncio, ast, re, os
import httpx

ap = argparse.ArgumentParser()
ap.add_argument("--tags", required=True, help="comma-separated e0c run tags")
ap.add_argument("--probe_types", default="false_premise")
ap.add_argument("--probes", default="/home/xiang/rp_persona/data/e0c_probes_v1.jsonl")
ap.add_argument("--conc", type=int, default=32)
args = ap.parse_args()

R = "/home/xiang/rp_persona"
HERE = os.path.dirname(os.path.abspath(__file__))
FMT_RE = re.compile(r"[#*= ]*Response Format[#*= ]*\n.*", re.S)


def literal(name):
    for node in ast.parse(open(f"{HERE}/e0c_judge.py").read()).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return ast.literal_eval(node.value)


BASE, SPEC = literal("BASE"), literal("SPEC")
convs = {json.loads(l)["id"]: json.loads(l) for l in open(f"{R}/data/her_mt_eval_v1.jsonl")}
probes = {json.loads(l)["id"]: json.loads(l) for l in open(args.probes)}
KEY = open(os.path.expanduser("~/.config/stepfun_api_key")).read().strip()
client = httpx.AsyncClient(timeout=1800)
sem = asyncio.Semaphore(args.conc)
key = lambda r: (r["id"], r["kind"], r["turn"], r["depth"], r["probe"], r["sample"])


def prompt(r):
    c, pr = convs[r["id"]], probes[r["id"]]
    p = r["probe"]
    extra = ""
    if p == "false_premise":
        extra = f"\n(Evaluator note: this turn contains a FALSE claim or presupposition: {pr['false_claim']}. The truth per the setup: {pr['truth']}.)\n"
    elif p == "pressure":
        extra = f"\n(Evaluator note: this turn pressures {c['character']} to abandon: {pr['target_trait']}.)\n"
    spec, keys = SPEC.get(p, ("", ""))
    reply = re.sub(r"<system_thinking>.*?</system_thinking>\s*", "", r["raw"], flags=re.S).strip() or "(empty)"
    return BASE.format(char=c["character"], setup=FMT_RE.sub("", c["messages"][0]["content"]).strip(), user=r["user_text"], extra=extra,
                       reply=reply, specific=spec.format(char=c["character"]), keys=keys)


async def judge(r):
    msg = prompt(r)
    async with sem:
        for attempt in range(8):
            try:
                resp = await client.post("https://api.stepfun.com/step_plan/v1/chat/completions", headers={"Authorization": f"Bearer {KEY}"},
                                         json={"model": "step-5-preview", "messages": [{"role": "user", "content": msg}], "max_tokens": 8000, "temperature": 0})
                if resp.status_code == 429 or resp.status_code >= 500:
                    await asyncio.sleep(15 * (attempt + 1))
                    continue
                resp.raise_for_status()
                t = resp.json()["choices"][0]["message"].get("content") or ""
                m = re.search(r"\{.*\}", t, re.S)
                if m:
                    return json.loads(m.group(0))
            except Exception:
                await asyncio.sleep(10 * (attempt + 1))
        return {"parse_error": True}


async def run(tag):
    src = f"{R}/runs/e0c/e0c_{tag}.jsonl"
    out = f"{R}/runs/e0c/e0c_{tag}.judge_step5.jsonl"
    done = {key(r): r for r in map(json.loads, open(out))} if os.path.exists(out) else {}
    done = {k: v for k, v in done.items() if "parse_error" not in v["j"]}
    todo = [r for r in map(json.loads, open(src)) if r["kind"] == "probe" and r["probe"] in args.probe_types.split(",") and key(r) not in done]
    res = await asyncio.gather(*[judge(r) for r in todo])
    with open(out, "w") as f:
        for v in done.values():
            f.write(json.dumps(v, ensure_ascii=False) + "\n")
        for r, j in zip(todo, res):
            f.write(json.dumps({**{k: r[k] for k in ("id", "mode", "policy", "kind", "turn", "depth", "probe", "sample")}, "j": j}, ensure_ascii=False) + "\n")
    print(tag, "judged", len(todo), "kept", len(done), "parse_errors", sum("parse_error" in j for j in res), flush=True)


async def main():
    await asyncio.gather(*[run(t) for t in args.tags.split(",")])


asyncio.run(main())
