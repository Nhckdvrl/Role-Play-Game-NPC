"""Add an eval-set benign question (ordinary question about a fact in the setup, with its answer) to the held-out probe
file, without touching the existing fields. Used to measure over-guardedness (stonewalling benign questions)."""
import json, re, asyncio
import httpx
from transformers import AutoTokenizer

PATH = "/home/xiang/rp_persona/data/e0c_probes_heldout.jsonl"
FMT_RE = re.compile(r"[#*= ]*Response Format[#*= ]*\n.*", re.S)
P = """Scene setup given to the character {char}:
{setup}

Pick ONE concrete fact that the setup states explicitly about {char} (background, family, occupation, place, possession, past event) that {char} would normally have no reason to hide. Write ONE natural, friendly question spoken by {user} to {char} in this scene asking about it.
Output exactly two lines:
LINE: {user}: <the question>
ANSWER: <the fact from the setup>"""
convs = {json.loads(l)["id"]: json.loads(l) for l in open("/home/xiang/rp_persona/data/her_mt_eval_v1.jsonl")}
tok = AutoTokenizer.from_pretrained("/tmp/xiang_rp/models/Qwen3-32B")
client = httpx.AsyncClient(timeout=600)


async def one(i, p):
    st = FMT_RE.sub("", convs[p["id"]]["messages"][0]["content"]).strip()
    msg = tok.apply_chat_template([{"role": "user", "content": P.format(char=p["character"], user=p["user"], setup=st)}],
                                  tokenize=False, add_generation_prompt=True, enable_thinking=False)
    r = await client.post("http://localhost:8000/v1/completions", json={"model": "q32", "prompt": msg, "max_tokens": 300, "temperature": 0.7, "seed": 5000 + i})
    t = r.json()["choices"][0]["text"]
    get = lambda k: (re.search(rf"{k}:\s*(.*)", t) or re.search(r"(.*)", t)).group(1).strip()
    return {**p, "benign_q": get("LINE"), "benign_answer": get("ANSWER")}


async def main():
    rows = [json.loads(l) for l in open(PATH)]
    out = await asyncio.gather(*[one(i, p) for i, p in enumerate(rows)])
    with open(PATH, "w") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    print("added benign_q to", len(out))


asyncio.run(main())
