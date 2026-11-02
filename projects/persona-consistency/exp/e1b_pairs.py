"""Build context-distillation training sets (E1b).

Target replies were generated WITH the re-anchoring cue (e1b_distill_data.py); training prompts are the SAME
contexts WITHOUT the cue, ending in the "<system_thinking>" prefill (completions start after it).
  distill_sft  every context with a non-failing cued reply -> SFT on (uncued prompt, cued reply)
  distill_dpo  contexts that also have a failing DEFAULT reply (from e1_data) -> chosen cued / rejected default
"""
import json, argparse, random, os
from transformers import AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--cued", default="/home/xiang/rp_persona/runs/e1/e1b_reanchor_v1.jsonl")
ap.add_argument("--default", default="/home/xiang/rp_persona/runs/e1/e1_data_v1.jsonl")
ap.add_argument("--out_dir", default="/home/xiang/rp_persona/data/e1b")
ap.add_argument("--tok", default="/tmp/xiang_rp/models/Qwen3-8B")
ap.add_argument("--max_prompt", type=int, default=7168)
args = ap.parse_args()

tok = AutoTokenizer.from_pretrained(args.tok)
rng = random.Random(0)
FAIL = {"false_premise": "accepted_false", "true_premise": "rejected_true"}
PREFILL = "<system_thinking>"


def failed(c, probe):
    j = c["j"]
    if "parse_error" in j or not c["format_ok"]:
        return None
    return j.get("in_character") == 0 or j.get(FAIL[probe]) == 1


def render(msgs):
    while True:
        p = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        if len(tok(p).input_ids) <= args.max_prompt or len(msgs) <= 4:
            return p + PREFILL
        msgs = [msgs[0]] + msgs[3:]


default = {(r["id"], r["depth"], r["probe"]): r for r in map(json.loads, open(args.default))}
sft, dpo = [], []
for r in map(json.loads, open(args.cued)):
    good = [c for c in r["cands"] if failed(c, r["probe"]) is False]
    if not good:
        continue
    best = max(good, key=lambda c: (c["j"].get("persona", 0), -c["k"]))
    prompt = render(r["messages"])
    sft.append({"prompt": prompt, "completion": best["raw"][len(PREFILL):], "id": r["id"], "probe": r["probe"]})
    d = default.get((r["id"], r["depth"], r["probe"]))
    bad = [c for c in d["cands"] if c["kind"] == "default" and failed(c, r["probe"]) is True] if d else []
    if bad:
        dpo.append({"prompt": prompt, "chosen": best["raw"][len(PREFILL):], "rejected": rng.choice(bad)["raw"][len(PREFILL):],
                    "id": r["id"], "probe": r["probe"]})
os.makedirs(args.out_dir, exist_ok=True)
for name, rows in (("distill_sft", sft), ("distill_dpo", dpo)):
    with open(f"{args.out_dir}/{name}.jsonl", "w") as f:
        for x in rows:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
print({"distill_sft": len(sft), "distill_dpo": len(dpo)})
