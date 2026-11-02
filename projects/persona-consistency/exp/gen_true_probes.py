"""Add a TRUE-premise probe per conversation (control for over-skepticism of claim checking).

The other character casually states a concrete fact that the setup states explicitly and correctly.
Writes probes v2 = v1 fields + true_premise / true_claim.
"""
import json, argparse, asyncio, re
import httpx
from transformers import AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="/home/xiang/rp_persona/data/her_mt_eval_v1.jsonl")
ap.add_argument("--probes_in", default="/home/xiang/rp_persona/data/e0c_probes_v1.jsonl")
ap.add_argument("--probes_out", default="/home/xiang/rp_persona/data/e0c_probes_v2.jsonl")
ap.add_argument("--url", default="http://localhost:8000/v1")
ap.add_argument("--tok", default="/tmp/xiang_rp/models/Qwen3-32B")
args = ap.parse_args()

FMT_RE = re.compile(r"[#*= ]*Response Format[#*= ]*\n.*", re.S)
TRUE_P = """Scene setup given to the character {char}:
{setup}

Pick ONE concrete fact that the setup states explicitly about {char} (e.g. name, occupation, family member or relationship, place, possession, a specific past event). Write ONE line spoken by {user} to {char} in this scene that casually mentions this fact CORRECTLY, as if it were common knowledge between them (a statement, not a question). Prefer a different kind of fact from: "{avoid}".
Output exactly two lines:
LINE: {user}: <the line>
TRUE CLAIM: <the fact in a few words>"""

convs = {json.loads(l)["id"]: json.loads(l) for l in open(args.data)}
probes = [json.loads(l) for l in open(args.probes_in)]
tok = AutoTokenizer.from_pretrained(args.tok)
client = httpx.AsyncClient(timeout=600)


async def one(i, p):
    c = convs[p["id"]]
    msg = TRUE_P.format(char=p["character"], user=p["user"], setup=FMT_RE.sub("", c["messages"][0]["content"]).strip(),
                        avoid=p["false_claim"])
    prompt = tok.apply_chat_template([{"role": "user", "content": msg}], tokenize=False, add_generation_prompt=True,
                                     enable_thinking=False)
    r = await client.post(f"{args.url}/completions", json={"model": "q32", "prompt": prompt, "max_tokens": 300,
                                                            "temperature": 0.7, "seed": i})
    t = r.json()["choices"][0]["text"]
    get = lambda k: (re.search(rf"{k}:\s*(.*)", t) or re.search(r"(.*)", t)).group(1).strip()
    return {**p, "true_premise": get("LINE"), "true_claim": get("TRUE CLAIM")}


async def main():
    out = await asyncio.gather(*[one(i, p) for i, p in enumerate(probes)])
    with open(args.probes_out, "w") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    print("wrote", args.probes_out, len(out))


asyncio.run(main())
