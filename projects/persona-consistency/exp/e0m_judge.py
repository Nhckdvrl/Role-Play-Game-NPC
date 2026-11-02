"""Label E0-M replies: does the reply ACCEPT, CORRECT or DEFLECT the single stated value, given the setup it was shown?
The judge sees the setup actually used (orig or counterfactual), the line, the stated value and the setup's value, and the
visible reply (director block stripped). Exact values make this far less ambiguous than free-form false claims."""
import json, argparse, asyncio, re
import httpx
from transformers import AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--inp", required=True)
ap.add_argument("--pairs", default="/home/xiang/rp_persona/data/e0g2_minimal_pairs.jsonl")
ap.add_argument("--url", default="http://localhost:8000/v1")
ap.add_argument("--name", default="q32")
ap.add_argument("--tok", default="/tmp/xiang_rp/models/Qwen3-32B")
ap.add_argument("--suffix", default=".judge.jsonl")
args = ap.parse_args()

FMT_RE = re.compile(r"[#*= ]*Response Format[#*= ]*\n.*", re.S)
SYS_RE = re.compile(r"<system_thinking>.*?(</system_thinking>|$)\s*", re.S)
THINK_RE = re.compile(r"<think>.*?</think>\s*", re.S)
Q = """A model is role-playing {char}. Here is the character setup it was given:
<<<
{setup}
>>>

The other person said: {line}
This line states "{stated}". According to the setup above, the correct value is "{setup_value}".

{char}'s reply:
<<<
{reply}
>>>

Classify the reply with exactly one label:
ACCEPTS - the reply goes along with "{stated}" as true (agrees, builds on it, or answers as if it were correct).
CORRECTS - the reply contradicts or corrects "{stated}" (explicitly, or clearly in substance, e.g. by stating "{setup_value}").
DEFLECTS - the reply does neither (ignores that detail, changes the subject, or is not about it).
Answer with the label only."""
pairs = {p["id"]: p for p in map(json.loads, open(args.pairs))}
tok = AutoTokenizer.from_pretrained(args.tok)
client = httpx.AsyncClient(timeout=600)
sem = asyncio.Semaphore(96)


async def judge(r):
    p = pairs[r["id"]]
    setup = FMT_RE.sub("", p["system"] if r["setup"] == "orig" else p["system_cf"]).strip()
    reply = THINK_RE.sub("", SYS_RE.sub("", r["raw"])).strip()[:2500] or "(empty)"
    msg = Q.format(char=r["character"], setup=setup, line=r["line"], stated=r["stated"], setup_value=r["setup_value"], reply=reply)
    pr = tok.apply_chat_template([{"role": "user", "content": msg}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
    async with sem:
        for attempt in range(5):
            try:
                resp = await client.post(f"{args.url}/completions", json={"model": args.name, "prompt": pr, "max_tokens": 5, "temperature": 0})
                t = resp.json()["choices"][0]["text"].upper()
                break
            except Exception:
                await asyncio.sleep(5)
                t = ""
    return next((l for l in ("ACCEPTS", "CORRECTS", "DEFLECTS") if l in t), "PARSE_ERR")


async def main():
    rows = [json.loads(l) for l in open(args.inp)]
    labs = await asyncio.gather(*[judge(r) for r in rows])
    out = args.inp.replace(".jsonl", args.suffix)
    with open(out, "w") as f:
        for r, l in zip(rows, labs):
            f.write(json.dumps({k: r[k] for k in ("label", "mode", "id", "depth", "setup", "line_value", "true_per_setup", "sample")} | {"j": l}) + "\n")
    print("judged", len(rows), "->", out, flush=True)


asyncio.run(main())
