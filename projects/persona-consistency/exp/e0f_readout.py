"""E0-F: is the truth still READABLE at depth even when it is not USED? (behavioural readout)

Context = E0-C self-generated history up to depth D + the premise probe line. Then an out-of-scene
verification question is appended as a new user turn, and we read P(Yes) vs P(No) for the first
answer token (vLLM logprobs, greedy, thinking off):
  false claim -> correct answer "No";  true claim -> correct answer "Yes".
Joined with E0-E judgements of the in-scene reply (same conversation, depth, probe) this gives,
per conversation, "knows the truth" vs "used it in the reply".
"""
import json, argparse, asyncio, math, re, os
import httpx
from transformers import AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--src", default="/home/xiang/rp_persona/runs/e0c/e0c_q8her.jsonl")
ap.add_argument("--data", default="/home/xiang/rp_persona/data/her_mt_eval_v1.jsonl")
ap.add_argument("--probes", default="/home/xiang/rp_persona/data/e0c_probes_v2_validated.jsonl")
ap.add_argument("--out", default="/home/xiang/rp_persona/runs/e0f/e0f_q8her.jsonl")
ap.add_argument("--url", default="http://localhost:8001/v1")
ap.add_argument("--tok", default="/tmp/xiang_rp/models/Qwen3-8B")
ap.add_argument("--depths", default="2,10,20")
args = ap.parse_args()

SYS_RE = re.compile(r"<system_thinking>.*?</system_thinking>\s*", re.S)
Q = ("(Out-of-scene check, answer as the system, not as the character: according to {char}'s setup above, is "
     "the following statement true? \"{claim}\" Answer with exactly one word, Yes or No.)")
tok = AutoTokenizer.from_pretrained(args.tok)
client = httpx.AsyncClient(timeout=600)
sem = asyncio.Semaphore(64)
convs = {json.loads(l)["id"]: json.loads(l) for l in open(args.data)}
probes = {json.loads(l)["id"]: json.loads(l) for l in open(args.probes)}
nat = {}
for r in map(json.loads, open(args.src)):
    if r["kind"] == "natural":
        nat.setdefault(r["id"], {})[r["turn"]] = r


async def readout(cid, depth, ptype):
    c, p = convs[cid], probes[cid]
    msgs = [c["messages"][0]]
    for t in range(depth):
        msgs += [{"role": "user", "content": nat[cid][t]["user_text"]},
                 {"role": "assistant", "content": SYS_RE.sub("", nat[cid][t]["raw"]).strip()}]
    claim = p["false_claim"] if ptype == "false_premise" else p["true_claim"]
    msgs.append({"role": "user", "content": p[ptype] + "\n\n" + Q.format(char=c["character"], claim=claim)})
    prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    async with sem:
        r = await client.post(f"{args.url}/completions", json={"model": "q8", "prompt": prompt, "max_tokens": 1,
                                                                "temperature": 0, "logprobs": 20})
    top = r.json()["choices"][0]["logprobs"]["top_logprobs"][0]
    py = sum(math.exp(v) for k, v in top.items() if k.strip().lower() == "yes")
    pn = sum(math.exp(v) for k, v in top.items() if k.strip().lower() == "no")
    correct = "no" if ptype == "false_premise" else "yes"
    pc = (pn if correct == "no" else py) / max(py + pn, 1e-9)
    return {"id": cid, "depth": depth, "probe": ptype, "p_yes": py, "p_no": pn, "p_correct": pc, "knows": pc > 0.5}


async def main():
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    jobs = [readout(cid, d, pt) for cid in sorted(nat) for d in map(int, args.depths.split(","))
            for pt in ("false_premise", "true_premise")]
    res = await asyncio.gather(*jobs)
    with open(args.out, "w") as f:
        for r in res:
            f.write(json.dumps(r) + "\n")
    print("wrote", args.out, len(res))


asyncio.run(main())
