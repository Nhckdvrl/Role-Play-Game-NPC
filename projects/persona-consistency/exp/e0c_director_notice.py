"""Did the HER director block (<system_thinking>) notice the false premise? (Qwen3-32B label)

Crossed with the reply-level accepted_false label this separates
  director miss    (director did not notice, reply accepted)
  handoff failure  (director noticed, reply still accepted)
"""
import json, argparse, asyncio, re
import httpx
from transformers import AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--gen", default="/home/xiang/rp_persona/runs/e0c/e0c_q8her.jsonl")
ap.add_argument("--probes", default="/home/xiang/rp_persona/data/e0c_probes_v1.jsonl")
ap.add_argument("--url", default="http://fvcrc10:8000/v1")
ap.add_argument("--tok", default="/tmp/xiang_rp/models/Qwen3-32B")
ap.add_argument("--suffix", default=".director_notice_strict.jsonl")
args = ap.parse_args()

Q = """A role-play model playing {char} first wrote a private planning note (below) before replying to this line:
LINE: {line}
This line contains a FALSE claim: {claim}. The truth according to {char}'s setup: {truth}.

Planning note:
<<<
{director}
>>>

Does the planning note EXPLICITLY address this claim — i.e. it explicitly states the true fact, or explicitly says the claim is wrong / mistaken / must be corrected? General character analysis that never mentions the claimed fact counts as NO. Answer with exactly one word: YES or NO."""

probes = {json.loads(l)["id"]: json.loads(l) for l in open(args.probes)}
rows = [r for r in map(json.loads, open(args.gen)) if r["kind"] == "probe" and r["probe"] == "false_premise"]
tok = AutoTokenizer.from_pretrained(args.tok)
client = httpx.AsyncClient(timeout=600)
sem = asyncio.Semaphore(64)


async def ask(r):
    p = probes[r["id"]]
    msg = Q.format(char=r["character"], line=p["false_premise"], claim=p["false_claim"], truth=p["truth"],
                   director=r["director"] or "(empty)")
    prompt = tok.apply_chat_template([{"role": "user", "content": msg}], tokenize=False, add_generation_prompt=True,
                                     enable_thinking=False)
    async with sem:
        resp = await client.post(f"{args.url}/completions",
                                 json={"model": "q32", "prompt": prompt, "max_tokens": 3, "temperature": 0})
    return "YES" in resp.json()["choices"][0]["text"].upper()


async def main():
    res = await asyncio.gather(*[ask(r) for r in rows])
    out = args.gen.replace(".jsonl", args.suffix)
    with open(out, "w") as f:
        for r, y in zip(rows, res):
            f.write(json.dumps({"id": r["id"], "depth": r["depth"], "sample": r["sample"], "noticed": y}) + "\n")
    print("wrote", out, len(rows))


asyncio.run(main())
