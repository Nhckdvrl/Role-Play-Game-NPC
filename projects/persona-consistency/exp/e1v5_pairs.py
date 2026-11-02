"""Round-3 DPO pairs from e1v5_data: like e1v4_pairs, plus assistant_task / none probes, hostility as failure,
and the chosen candidate = the highest-persona non-failing one.

Round-2 DPO pairs from e1v4_data: per context, non-failing vs failing candidates of the round-1 policy.

failure = out of character OR the probe-specific failure (accepted_false / rejected_true / caved / revealed_ai).
Prompt includes the "<system_thinking>" prefill; completions start after it (same convention as e1_pairs.py).
"""
import json, argparse, random, collections, os
from transformers import AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="/home/xiang/rp_persona/runs/e1/e1v5_data.jsonl")
ap.add_argument("--out", default="/home/xiang/rp_persona/data/e1v5/dpo_r3.jsonl")
ap.add_argument("--tok", default="/tmp/xiang_rp/models/Qwen3-8B")
ap.add_argument("--max_prompt", type=int, default=7168)
ap.add_argument("--per_ctx", type=int, default=2)
args = ap.parse_args()

FAIL = {"false_premise": "accepted_false", "true_premise": "rejected_true", "pressure": "caved", "meta_ai": "revealed_ai",
        "assistant_task": "complied", "none": "generic", "benign_q": "evasive"}
YIELD = {"ooc_ai": "honest_disclosure", "ooc_req": "honored"}   # should-yield probes: stepping out is the success
PREFILL = "<system_thinking>"
tok = AutoTokenizer.from_pretrained(args.tok)
rng = random.Random(0)


def failed(c, p):
    j = c["j"]
    if "parse_error" in j or not c["format_ok"]:
        return None
    if p in YIELD:
        return j.get(YIELD[p]) != 1 or j.get("hostile") == 1
    return j.get("in_character") == 0 or j.get(FAIL[p]) == 1 or j.get("hostile") == 1


def render(msgs):
    while True:
        s = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        if len(tok(s).input_ids) <= args.max_prompt or len(msgs) <= 4:
            return s + PREFILL
        msgs = [msgs[0]] + msgs[3:]


rows, stats = [], collections.Counter()
for r in map(json.loads, open(args.data)):
    p = r["probe"]
    lab = [(c, failed(c, p)) for c in r["cands"]]
    good = [c for c, f in lab if f is False]
    bad = [c for c, f in lab if f is True]
    stats[(p, "ctx")] += 1
    stats[(p, "n")] += sum(f is not None for _, f in lab)
    stats[(p, "fail")] += len(bad)
    if not good or not bad:
        continue
    stats[(p, "usable")] += 1
    prompt = render(r["messages"])
    for k in range(min(args.per_ctx, len(bad))):
        pick = rng.choice(good) if p in YIELD else max(good, key=lambda c: (c["j"].get("persona", 0), rng.random()))
        rows.append({"prompt": prompt, "chosen": pick["raw"][len(PREFILL):], "rejected": bad[k]["raw"][len(PREFILL):],
                     "id": r["id"], "depth": r["depth"], "probe": p})
os.makedirs(os.path.dirname(args.out), exist_ok=True)
with open(args.out, "w") as f:
    for x in rows:
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
for p in list(FAIL) + list(YIELD):
    print(p, f"fail rate {stats[(p, 'fail')] / max(1, stats[(p, 'n')]):.3f}", f"usable ctx {stats[(p, 'usable')]}/{stats[(p, 'ctx')]}")
print("pairs", len(rows), collections.Counter(x["probe"] for x in rows))
