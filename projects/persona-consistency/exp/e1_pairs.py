"""Build E1 training sets from e1_data candidates.

failure(c): out of character, or the probe-specific failure (accepted_false / rejected_true).
Arms (matched number of examples, same rejected pool):
  dpo_implicit  chosen = non-failing DEFAULT-prefill sample (natural director), rejected = failing default sample
  dpo_explicit  chosen = non-failing SELF-CHECK sample whose director actually found the conflict and stated the
                true fact (dir_outcome == FOUND_CORRECT; for true-premise contexts any non-failing self-check sample),
                rejected = failing default
  sft_rft       chosen of dpo_implicit only (rejection-sampling SFT baseline)
  dpo_implicit_all  like dpo_implicit but from EVERY context with a good and a bad default sample (more data,
                    not context-matched to dpo_explicit)
Prompts are rendered with the policy chat template and trimmed (oldest exchanges first) to fit. The
"<system_thinking>" prefill belongs to the PROMPT (as at inference): completions start right after it, so
prompt and completion token boundaries match generation (">" + "\n..." rather than a merged ">\n" token).
"""
import json, argparse, random, collections, os
from transformers import AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="/home/xiang/rp_persona/runs/e1/e1_data_v1.jsonl")
ap.add_argument("--out_dir", default="/home/xiang/rp_persona/data/e1")
ap.add_argument("--tok", default="/tmp/xiang_rp/models/Qwen3-8B")
ap.add_argument("--max_prompt", type=int, default=7168)
ap.add_argument("--per_ctx", type=int, default=2)
ap.add_argument("--seed", type=int, default=0)
args = ap.parse_args()

tok = AutoTokenizer.from_pretrained(args.tok)
rng = random.Random(args.seed)
FAIL = {"false_premise": "accepted_false", "true_premise": "rejected_true"}


def failed(c, probe):
    j = c["j"]
    if "parse_error" in j or not c["format_ok"]:
        return None
    return j.get("in_character") == 0 or j.get(FAIL[probe]) == 1


PREFILL = "<system_thinking>"


def render(msgs):
    while True:
        p = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        if len(tok(p).input_ids) <= args.max_prompt or len(msgs) <= 4:
            return p + PREFILL
        msgs = [msgs[0]] + msgs[3:]


def cut(raw):
    assert raw.startswith(PREFILL), raw[:40]
    return raw[len(PREFILL):]


arms = collections.defaultdict(list)
stats = collections.Counter()
for r in map(json.loads, open(args.data)):
    p = r["probe"]
    lab = [(c, failed(c, p)) for c in r["cands"]]
    good_def = [c for c, f in lab if f is False and c["kind"] == "default"]
    good_sc = [c for c, f in lab if f is False and c["kind"] == "selfcheck"
               and (p != "false_premise" or c.get("dir_outcome") == "FOUND_CORRECT")]
    bad_def = [c for c, f in lab if f is True and c["kind"] == "default"]
    stats[(p, "ctx")] += 1
    stats[(p, "def_fail")] += sum(1 for c, f in lab if c["kind"] == "default" and f is True)
    stats[(p, "def_n")] += sum(1 for c, f in lab if c["kind"] == "default" and f is not None)
    stats[(p, "sc_fail")] += sum(1 for c, f in lab if c["kind"] == "selfcheck" and f is True)
    stats[(p, "sc_n")] += sum(1 for c, f in lab if c["kind"] == "selfcheck" and f is not None)
    if bad_def and good_def:
        prompt = render(r["messages"])
        for k in range(min(args.per_ctx, len(bad_def))):
            arms["dpo_implicit_all"].append({"prompt": prompt, "chosen": cut(rng.choice(good_def)["raw"]), "rejected": cut(bad_def[k]["raw"]),
                                             "id": r["id"], "depth": r["depth"], "probe": p})
    if not bad_def or not good_def or not good_sc:
        continue  # keep only contexts usable by BOTH arms so the arms see the same contexts
    stats[(p, "usable")] += 1
    prompt = render(r["messages"])
    for k in range(min(args.per_ctx, len(bad_def))):
        rej = cut(bad_def[k]["raw"])
        meta = {"id": r["id"], "depth": r["depth"], "probe": p}
        arms["dpo_implicit"].append({"prompt": prompt, "chosen": cut(rng.choice(good_def)["raw"]), "rejected": rej, **meta})
        arms["dpo_explicit"].append({"prompt": prompt, "chosen": cut(rng.choice(good_sc)["raw"]), "rejected": rej, **meta})
arms["sft_rft"] = [{"prompt": x["prompt"], "completion": x["chosen"], "id": x["id"], "probe": x["probe"]}
                   for x in arms["dpo_implicit"]]

os.makedirs(args.out_dir, exist_ok=True)
for name, rows in arms.items():
    with open(f"{args.out_dir}/{name}.jsonl", "w") as f:
        for x in rows:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
for p in FAIL:
    print(p, {k[1]: v for k, v in stats.items() if k[0] == p},
          f"default fail rate {stats[(p, 'def_fail')] / max(1, stats[(p, 'def_n')]):.3f}",
          f"selfcheck fail rate {stats[(p, 'sc_fail')] / max(1, stats[(p, 'sc_n')]):.3f}")
print({k: len(v) for k, v in arms.items()}, "examples;",
      len({x["id"] for x in arms["dpo_implicit"]}), "conversations")
