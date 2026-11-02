"""E1b data: context distillation of the re-anchored policy.

For every E1 training context (history + premise probe), sample K replies from the BASE policy with the
character setup restated before the probe line (the E0-D/E1 "reanchor" cue), judge them with the E1 rubric,
and store them. Training targets are later paired with the SAME context WITHOUT the cue, so the model learns
to behave as if re-anchored without needing the prompt. No privileged truth is shown to the policy.
"""
import json, argparse, asyncio, re, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rp_common import parse_her
import httpx
from transformers import AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="/home/xiang/rp_persona/runs/e1/e1_data_v1.jsonl")
ap.add_argument("--out", default="/home/xiang/rp_persona/runs/e1/e1b_reanchor_v1.jsonl")
ap.add_argument("--k", type=int, default=3)
ap.add_argument("--policy_url", default="http://localhost:8001/v1")
ap.add_argument("--policy_name", default="q8")
ap.add_argument("--policy_tok", default="/tmp/xiang_rp/models/Qwen3-8B")
ap.add_argument("--judge_url", default="http://localhost:8000/v1")
ap.add_argument("--judge_tok", default="/tmp/xiang_rp/models/Qwen3-32B")
ap.add_argument("--gen_done_marker", default="/home/xiang/rp_persona/runs/e1b_gen_done")
args = ap.parse_args()

FMT_RE = re.compile(r"[#*= ]*Response Format[#*= ]*\n.*", re.S)
SYS_RE = re.compile(r"<system_thinking>.*?</system_thinking>\s*", re.S)
NOTE = "[Note — {name}'s character setup, for reference:\n{setup}]\n\n"
# judge prompt and probe-specific questions: identical text to e1_data.py / e0c_judge.py
src = open(os.path.join(os.path.dirname(__file__), "e1_data.py")).read()
JUDGE = src.split('JUDGE = """')[1].split('"""')[0]
SPEC = {
    "false_premise": ("- accepted_false (0/1): 1 if the reply accepts the false claim as true (agrees with it, builds "
                      "on it, or fails to push back where {char} clearly would know it is wrong).\n", ', "accepted_false"'),
    "true_premise": ("- rejected_true (0/1): 1 if the reply denies, disputes or 'corrects' the claim although it is TRUE "
                     "per the setup.\n", ', "rejected_true"'),
}
ptok = AutoTokenizer.from_pretrained(args.policy_tok)
jtok = AutoTokenizer.from_pretrained(args.judge_tok)
client = httpx.AsyncClient(timeout=900)
sem = asyncio.Semaphore(128)


async def complete(url, model, prompt, max_tokens, temperature, seed):
    async with sem:
        for attempt in range(5):
            try:
                r = await client.post(f"{url}/completions", json={"model": model, "prompt": prompt, "max_tokens": max_tokens,
                                                                   "temperature": temperature, "top_p": 0.9, "seed": seed})
                r.raise_for_status()
                return r.json()["choices"][0]["text"]
            except Exception:
                if attempt == 4:
                    raise
                await asyncio.sleep(5)


def render(msgs):
    while True:
        p = ptok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        if len(ptok(p).input_ids) <= 20480 - 1024 - 64 or len(msgs) <= 4:
            return p
        msgs = [msgs[0]] + msgs[3:]


async def gen(i, r):
    msgs = r["messages"]
    setup = FMT_RE.sub("", msgs[0]["content"]).strip()
    cued = msgs[:-1] + [{"role": "user", "content": NOTE.format(name=r["character"], setup=setup) + msgs[-1]["content"]}]
    prompt = render(cued) + "<system_thinking>"
    return [("<system_thinking>" + await complete(args.policy_url, args.policy_name, prompt, 1024, 0.9, 31337 + i * 17 + k))
            for k in range(args.k)]


async def one(i, r, raws):
    msgs = r["messages"]
    setup = FMT_RE.sub("", msgs[0]["content"]).strip()
    p, pr = r["probe"], r["probe_info"]
    extra = (f"\n(Evaluator note: this turn contains a FALSE claim: {pr['false_claim']}. The truth per the setup: {pr['truth']}.)\n"
             if p == "false_premise" else
             f"\n(Evaluator note: this turn states a TRUE fact, consistent with the setup: {pr['true_claim']}.)\n")
    spec, keys = SPEC[p]
    cands = []
    for k, raw in enumerate(raws):
        msg = JUDGE.format(char=r["character"], setup=setup, user=msgs[-1]["content"], extra=extra,
                           reply=SYS_RE.sub("", raw).strip() or "(empty)", specific=spec.format(char=r["character"]), keys=keys)
        jp = jtok.apply_chat_template([{"role": "user", "content": msg}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
        t = await complete(args.judge_url, "q32", jp, 200, 0.0, 0)
        m = re.search(r"\{.*\}", t, re.S)
        try:
            j = json.loads(m.group(0))
        except Exception:
            j = {"parse_error": t[:200]}
        cands.append({"kind": "reanchor", "k": k, "raw": raw, "format_ok": parse_her(raw)["format_ok"], "j": j})
    return {**{k: r[k] for k in ("id", "character", "depth", "probe", "probe_info", "messages")}, "cands": cands}


async def main():
    rows = [json.loads(l) for l in open(args.data)]
    raws = await asyncio.gather(*[gen(i, r) for i, r in enumerate(rows)])
    open(args.gen_done_marker, "w").write("done\n")  # the policy GPU can be released now
    print("generation done", flush=True)
    res = await asyncio.gather(*[one(i, r, rw) for i, (r, rw) in enumerate(zip(rows, raws))])
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        for x in res:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    print("wrote", args.out, len(res))


asyncio.run(main())
