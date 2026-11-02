"""Export the curated, small, redistributable data of this subproject into ../data/ (committed to Git).

Not exported (kept outside Git, under ~/rp_persona): raw generations, model weights / LoRA adapters, HF caches, and full
HER / APC source texts (rebuild them from the public datasets by id). Exported:
  splits.jsonl                 eval / train conversation ids (HER multi-turn), work and character names only
  probes_closed_loop.jsonl     probe set used in every closed-loop run (E0-C protocol)
  probes_full.jsonl            superset: validity flags, held-out styles, benign questions, OOC probes
  minimal_pairs.jsonl          E0-G v2 / E0-M exact-value minimal pairs (setup texts removed; cf setup = string replace)
  audit/human_blind_labels_set{1,2}.jsonl  88 blind human labels (judge-validity audit)
  labels/false_premise_step5_judge.jsonl.gz  false-premise labels from the human-validated judge (step-5-preview)
Labels from the original, unvalidated judges (Qwen3-32B non-thinking, Mistral-Small) are NOT exported: the audit showed
they miss most acceptances of false claims.
"""
import json, gzip, os, glob

R = os.path.expanduser("~/rp_persona")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
os.makedirs(f"{OUT}/audit", exist_ok=True)
os.makedirs(f"{OUT}/labels", exist_ok=True)


def rows(path):
    return [json.loads(l) for l in open(path)]


with open(f"{OUT}/splits.jsonl", "w") as f:
    for split, path in (("eval", f"{R}/data/her_mt_eval_v1.jsonl"), ("train", f"{R}/data/her_mt_train_v1.jsonl")):
        for c in rows(path):
            f.write(json.dumps({"split": split, "id": c["id"], "work": c.get("work"), "character": c.get("character")}, ensure_ascii=False) + "\n")

for src, dst in (("e0c_probes_v1.jsonl", "probes_closed_loop.jsonl"), ("e0c_probes_ooc.jsonl", "probes_full.jsonl")):
    with open(f"{OUT}/{dst}", "w") as f:
        for r in rows(f"{R}/data/{src}"):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

with open(f"{OUT}/minimal_pairs.jsonl", "w") as f:
    for r in rows(f"{R}/data/e0g2_minimal_pairs.jsonl"):
        f.write(json.dumps({k: r[k] for k in ("split", "id", "character", "user", "value", "alternative", "line")}, ensure_ascii=False) + "\n")

def write_human(src_json, dst):
    with open(f"{OUT}/audit/{dst}", "w") as f:
        for h in json.load(open(src_json)):
            f.write(json.dumps({"k": h["k"], "run": h["tag"], "id": h["id"], "depth": h["depth"], "sample": h["sample"], "human": h["human"],
                                "legend": "A accepts false claim / C corrects / D deflects / N not a clear false claim in context"}) + "\n")


write_human(f"{R}/runs/audit/blind_human.json", "human_blind_labels_set1.jsonl")      # base, D2 + D20
write_human(f"{R}/runs/audit/blind2_human.json", "human_blind_labels_set2.jsonl")     # base / r2'-2ep / r2'', D20

# false-premise labels from the human-validated judge (step-5-preview, original rubric): base x3 closed loops + r2'-2ep
with gzip.open(f"{OUT}/labels/false_premise_step5_judge.jsonl.gz", "wt") as f:
    for run in ("q8her", "q8her_s1", "q8her_s2", "r2p2_her"):
        for r in rows(f"{R}/runs/e0c/e0c_{run}.judge_step5.jsonl"):
            f.write(json.dumps({"run": run, **{k: r.get(k) for k in ("id", "depth", "sample")},
                                "accepted_false": r["j"].get("accepted_false"), "in_character": r["j"].get("in_character")}) + "\n")
print("done ->", os.path.abspath(OUT))
