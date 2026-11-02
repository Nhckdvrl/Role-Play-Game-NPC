"""E0-G v2 step 1: counterfactual setups for minimal-pair conflict probing.

For each conversation with a true-premise line, Qwen3-32B rewrites the setup MINIMALLY so that the fact
stated by that line becomes different. Then the identical line is TRUE under the original setup and FALSE
under the edited one. A YES/NO check verifies both directions; only verified pairs are kept.
"""
import json, argparse, asyncio, re
import httpx
from transformers import AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--inputs", nargs="+", default=["/home/xiang/rp_persona/runs/e1/e1_data_v1.jsonl",
                                                "/home/xiang/rp_persona/data/e0c_probes_v2_validated.jsonl"])
ap.add_argument("--eval_data", default="/home/xiang/rp_persona/data/her_mt_eval_v1.jsonl")
ap.add_argument("--out", default="/home/xiang/rp_persona/data/e0g2_counterfactual_setups.jsonl")
ap.add_argument("--url", default="http://localhost:8000/v1")
ap.add_argument("--tok", default="/tmp/xiang_rp/models/Qwen3-32B")
args = ap.parse_args()

FMT_RE = re.compile(r"([#*= ]*Response Format[#*= ]*\n.*)", re.S)
EDIT = """Below is a character setup for {char}. Rewrite it MINIMALLY so that the following fact becomes different: "{fact}".
Choose one plausible different value for that fact and change only the words needed (also adjust any other sentence that would otherwise still state the original fact). Keep everything else word-for-word identical.
Output ONLY the full rewritten setup, nothing else.

=== Setup ===
{setup}"""
CHECK = """Character setup for {char}:
{setup}

Line spoken to {char}: {line}

Is EVERYTHING this line asserts about {char} consistent with the setup above? Answer YES or NO."""

tok = AutoTokenizer.from_pretrained(args.tok)
client = httpx.AsyncClient(timeout=900)
sem = asyncio.Semaphore(48)


async def gen(msg, max_tokens):
    p = tok.apply_chat_template([{"role": "user", "content": msg}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
    async with sem:
        r = await client.post(f"{args.url}/completions", json={"model": "q32", "prompt": p, "max_tokens": max_tokens, "temperature": 0})
    return r.json()["choices"][0]["text"]


async def one(item):
    system = item["system"]
    m = FMT_RE.search(system)
    setup, fmt = (system[:m.start()], m.group(1)) if m else (system, "")
    new_setup = (await gen(EDIT.format(char=item["character"], fact=item["true_claim"], setup=setup.strip()), 4096)).strip()
    true_under_orig = "YES" in (await gen(CHECK.format(char=item["character"], setup=setup, line=item["line"]), 3)).upper()
    true_under_new = "YES" in (await gen(CHECK.format(char=item["character"], setup=new_setup, line=item["line"]), 3)).upper()
    ok = true_under_orig and not true_under_new and 0.6 < len(new_setup) / max(1, len(setup.strip())) < 1.4
    return {**item, "system_cf": new_setup + ("\n\n" + fmt if fmt else ""), "verified": ok,
            "true_under_orig": true_under_orig, "true_under_new": true_under_new}


async def main():
    items, seen = [], set()
    evalc = {json.loads(l)["id"]: json.loads(l) for l in open(args.eval_data)}
    for path in args.inputs:
        for r in map(json.loads, open(path)):
            if "probe_info" in r:  # E1 training data (one record per context; take each conversation once)
                if r["id"] in seen or r["probe"] != "true_premise":
                    continue
                seen.add(r["id"])
                items.append({"split": "train", "id": r["id"], "character": r["character"], "system": r["messages"][0]["content"],
                              "line": r["probe_info"]["true_premise"], "true_claim": r["probe_info"]["true_claim"]})
            else:  # eval probes
                items.append({"split": "eval", "id": r["id"], "character": r["character"],
                              "system": evalc[r["id"]]["messages"][0]["content"], "line": r["true_premise"],
                              "true_claim": r["true_claim"]})
    out = await asyncio.gather(*[one(it) for it in items])
    with open(args.out, "w") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    for s in ("train", "eval"):
        v = [o for o in out if o["split"] == s]
        print(s, "verified", sum(o["verified"] for o in v), "/", len(v))


asyncio.run(main())
