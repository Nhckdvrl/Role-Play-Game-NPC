"""E0-G v2: string-level minimal pairs for setup/claim conflict probing.

Qwen3-32B proposes candidates (VALUE verbatim in the setup, ALTERNATIVE value, LINE spoken by the other
character that contains VALUE explicitly). Counterfactual setup = setup with every occurrence of VALUE
replaced by ALTERNATIVE (exact string replacement, no rewriting). The same LINE is then TRUE under the
original setup and FALSE under the counterfactual one.
"""
import json, argparse, asyncio, re
import httpx
from transformers import AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--train", default="/home/xiang/rp_persona/runs/e1/e1_data_v1.jsonl")
ap.add_argument("--eval_data", default="/home/xiang/rp_persona/data/her_mt_eval_v1.jsonl")
ap.add_argument("--out", default="/home/xiang/rp_persona/data/e0g2_minimal_pairs.jsonl")
ap.add_argument("--url", default="http://localhost:8000/v1")
ap.add_argument("--tok", default="/tmp/xiang_rp/models/Qwen3-32B")
args = ap.parse_args()

FMT_RE = re.compile(r"[#*= ]*Response Format[#*= ]*\n.*", re.S)
PROPOSE = """Character setup for {char}:
{setup}

Propose 3 concrete facts about {char} whose value is written VERBATIM in the setup (a name, place, occupation, object, number...). For each give:
- "value": the exact substring copied from the setup (2-40 characters, must appear verbatim),
- "alternative": a plausible different value of the same type,
- "line": one natural line spoken by {user} to {char} in this scene that explicitly contains "value" verbatim and states it as a fact about {char}.
Output only a JSON list of 3 objects with keys value, alternative, line."""

tok = AutoTokenizer.from_pretrained(args.tok)
client = httpx.AsyncClient(timeout=900)
sem = asyncio.Semaphore(48)


def user_name(msgs):
    first = next(m["content"] for m in msgs if m["role"] == "user")
    m = re.match(r"\s*([^:\n<]{1,60}):", first)
    return m.group(1).strip() if m else "Stranger"


async def one(split, cid, char, msgs):
    setup = FMT_RE.sub("", msgs[0]["content"])
    us = user_name(msgs)
    p = tok.apply_chat_template([{"role": "user", "content": PROPOSE.format(char=char, user=us, setup=setup.strip())}],
                                tokenize=False, add_generation_prompt=True, enable_thinking=False)
    async with sem:
        r = await client.post(f"{args.url}/completions", json={"model": "q32", "prompt": p, "max_tokens": 800, "temperature": 0})
    t = r.json()["choices"][0]["text"]
    try:
        cands = json.loads(re.search(r"\[.*\]", t, re.S).group(0))
    except Exception:
        cands = []
    for c in cands:
        v, a, line = str(c.get("value", "")), str(c.get("alternative", "")), str(c.get("line", ""))
        if 2 <= len(v) <= 40 and v in setup and v in line and a and a != v and a not in setup:
            sys_cf = msgs[0]["content"].replace(v, a)
            return {"split": split, "id": cid, "character": char, "user": us, "value": v, "alternative": a,
                    "line": line, "system": msgs[0]["content"], "system_cf": sys_cf}
    return None


async def main():
    jobs, seen = [], set()
    for r in map(json.loads, open(args.train)):
        if r["id"] not in seen:
            seen.add(r["id"])
            jobs.append(one("train", r["id"], r["character"], r["messages"]))
    for c in map(json.loads, open(args.eval_data)):
        jobs.append(one("eval", c["id"], c["character"], c["messages"]))
    res = [x for x in await asyncio.gather(*jobs) if x]
    with open(args.out, "w") as f:
        for x in res:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    print("pairs", {s: sum(x["split"] == s for x in res) for s in ("train", "eval")})


asyncio.run(main())
