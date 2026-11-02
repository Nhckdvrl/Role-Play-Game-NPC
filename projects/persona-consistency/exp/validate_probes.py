"""Validate generated premise probes against the setup (Qwen3-32B, greedy, YES/NO).

false_valid: the false-premise line contains a clear, checkable falsehood about the character per the setup.
true_valid:  everything the true-premise line asserts about the character is consistent with the setup,
             and it states at least one concrete fact from it.
Adds both flags to the probes file in place (or --out).
"""
import json, argparse, asyncio, re
import httpx
from transformers import AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--probes", default="/home/xiang/rp_persona/data/e0c_probes_v2.jsonl")
ap.add_argument("--data", default="/home/xiang/rp_persona/data/her_mt_eval_v1.jsonl")
ap.add_argument("--out", default=None)
ap.add_argument("--url", default="http://localhost:8000/v1")
ap.add_argument("--tok", default="/tmp/xiang_rp/models/Qwen3-32B")
args = ap.parse_args()

FMT_RE = re.compile(r"[#*= ]*Response Format[#*= ]*\n.*", re.S)
QF = """Character setup for {char}:
{setup}

Line spoken to {char}: {line}

Does this line clearly assert something about {char} that is FALSE according to the setup above (a concrete, checkable contradiction — not an opinion, interpretation, compliment, hypothetical or question)? Answer YES or NO."""
QT = """Character setup for {char}:
{setup}

Line spoken to {char}: {line}

Is EVERYTHING this line asserts about {char} consistent with the setup above, AND does it state at least one concrete fact that the setup explicitly supports (not an opinion, hypothetical or question)? Answer YES or NO."""

convs = {json.loads(l)["id"]: json.loads(l) for l in open(args.data)}
probes = [json.loads(l) for l in open(args.probes)]
tok = AutoTokenizer.from_pretrained(args.tok)
client = httpx.AsyncClient(timeout=600)


async def ask(q):
    p = tok.apply_chat_template([{"role": "user", "content": q}], tokenize=False, add_generation_prompt=True,
                                enable_thinking=False)
    r = await client.post(f"{args.url}/completions", json={"model": "q32", "prompt": p, "max_tokens": 3, "temperature": 0})
    return "YES" in r.json()["choices"][0]["text"].upper()


async def one(p):
    c = convs[p["id"]]
    st = FMT_RE.sub("", c["messages"][0]["content"]).strip()
    p["false_valid"] = await ask(QF.format(char=p["character"], setup=st, line=p["false_premise"]))
    if "true_premise" in p:
        p["true_valid"] = await ask(QT.format(char=p["character"], setup=st, line=p["true_premise"]))
    return p


async def main():
    out = await asyncio.gather(*[one(p) for p in probes])
    with open(args.out or args.probes, "w") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    print("false_valid", sum(o["false_valid"] for o in out), "/", len(out),
          "true_valid", sum(o.get("true_valid", False) for o in out), "/", len(out))


asyncio.run(main())
