"""Export the curated, small, redistributable data of this subproject into ../data/ (committed to Git).

Not exported (kept outside Git, under ~/rp_persona): raw generations, model weights / LoRA adapters, HF caches, and full
HER / APC source texts (rebuild them from the public datasets by id). Exported:
  splits.jsonl                 eval / train conversation ids (HER multi-turn), work and character names only
  probes_closed_loop.jsonl     probe set used in every closed-loop run (E0-C protocol)
  probes_full.jsonl            superset: validity flags, held-out styles, benign questions, OOC probes
  minimal_pairs.jsonl          E0-G v2 / E0-M exact-value minimal pairs (setup texts removed; cf setup = string replace)
  audit/human_blind_labels.jsonl  48 blind human labels used to audit the accommodation judge
  labels/*.jsonl.gz            per-item judge labels (no texts) for the main closed-loop / fixed-history / P1 runs
  coser_scene_scores.jsonl     CoSER GCA per-scene dimension scores for each actor
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

key = {k["k"]: k for k in rows(f"{R}/runs/audit/blind_key.jsonl")}
with open(f"{OUT}/audit/human_blind_labels.jsonl", "w") as f:
    for h in json.load(open(f"{R}/runs/audit/blind_human.json")):
        f.write(json.dumps({"k": h["k"], "run": h["tag"], "id": h["id"], "depth": h["depth"], "sample": h["sample"], "human": h["human"],
                            "legend": "A accepts false claim / C corrects / D deflects / N not a clear false claim in context"}) + "\n")


def strip(j):
    return {k: v for k, v in j.items() if k != "reason"} if isinstance(j, dict) else j


def dump(name, paths):
    n = 0
    with gzip.open(f"{OUT}/labels/{name}.jsonl.gz", "wt") as f:
        for p in paths:
            if not os.path.exists(p):
                continue
            run = os.path.basename(p).replace(".jsonl", "")
            for r in rows(p):
                f.write(json.dumps({"run": run, **{k: r.get(k) for k in ("id", "kind", "turn", "depth", "probe", "sample", "policy")}, "j": strip(r.get("j"))}) + "\n")
                n += 1
    print(name, n)


E0C = ["q8her", "q8her_s1", "q8her_s2", "q8plain", "q14her", "her32", "her32_d20", "impall2_her", "impall2_her_s1", "impall2_her_s2", "ddpo_her",
       "r2_her", "r3_her", "r3b_her", "r2p_her", "r2p2_her", "r2pp_her", "r2pps1_her", "q8her_msim", "r2p2_msim", "r2pp_msim"]
dump("closed_loop_qwen32_judge", [f"{R}/runs/e0c/e0c_{t}.judge.jsonl" for t in E0C])
dump("closed_loop_mistral_judge", [f"{R}/runs/e0c/e0c_{t}.judge_mistral.jsonl" for t in E0C])
dump("fixed_history", sorted(glob.glob(f"{R}/runs/e1/evalv*_d20.judge.jsonl") + glob.glob(f"{R}/runs/e1/base_supp_d20.judge.jsonl")))
dump("heldout_benign", sorted(glob.glob(f"{R}/runs/e1/heldout_*_d20.judge.jsonl") + glob.glob(f"{R}/runs/e1/benign_*_d20.judge.jsonl")))
dump("p1_selectivity", sorted(glob.glob(f"{R}/runs/e1/p1_*_d20.judge.jsonl")))
dump("e0d_mechanism", sorted(glob.glob(f"{R}/runs/e0d/*.judge.jsonl")))

with open(f"{OUT}/coser_scene_scores.jsonl", "w") as f:
    for p in sorted(glob.glob(f"{R}/runs/coser/eval_*.json")):
        actor = os.path.basename(p)[5:-5]
        for e in json.load(open(p)):
            f.write(json.dumps({"actor": actor, "idx": e["idx"], "book": e["book"], "scores": e["scores"], "actor_rounds": e["actor_rounds"]}, ensure_ascii=False) + "\n")
print("done ->", os.path.abspath(OUT))
