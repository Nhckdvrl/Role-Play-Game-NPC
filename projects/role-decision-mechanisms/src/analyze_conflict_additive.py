"""Does a logit-additive model predict the conflict results?
From the T set (single-source conditions): d_self, d_other, d_world, d_told (logit effects of each source alone).
Prediction for own v + opposite X: d_self - d_X. Observed: logit effect in T-conflict. Same families/templates/rendering.
usage: analyze_conflict_additive.py TAG [...]"""
import json, sys
from collections import defaultdict

def load(prompts, run):
    meta = {}
    for l in open(prompts):
        r = json.loads(l); r.pop("messages"); meta[r["id"]] = r
    acc = defaultdict(list)
    for l in open(run):
        o = json.loads(l); m = meta[o["id"]]
        a, b = (o["lpA"], o["lpB"]) if m["pos_letter"] == "A" else (o["lpB"], o["lpA"])
        task = "K" if m["mode"] == "K" else "dec"
        acc[(task, m["fmt"], m["mode"], m["conv"], m["family"], m["valence"], m["owner"], m["form"])].append(max(min(a - b, 15), -15))
    return {k: sum(v) / len(v) for k, v in acc.items()}

def eff(c, task, o, f):
    v = [c[k] - c[k[:5] + ("neg", o, f)] for k in c if k[0] == task and k[5] == "pos" and k[6] == o and k[7] == f and k[:5] + ("neg", o, f) in c]
    return sum(v) / len(v)

for tag in sys.argv[1:]:
    big = tag in ("qwen3_14b", "qwen3_32b")
    t = load("/home/xiang/rp_mech/test/data/prompts.jsonl", f"/home/xiang/rp_mech/scale2/T_{tag}.jsonl" if big else f"/home/xiang/rp_mech/test/runs/{tag}.jsonl")
    cf = load("/home/xiang/rp_mech/test_conf/data/prompts.jsonl", f"/home/xiang/rp_mech/scale2/conf_{tag}.jsonl" if big else f"/home/xiang/rp_mech/test_conf/runs/{tag}.jsonl")
    print(f"\n## {tag}")
    for task in ("K", "dec"):
        ds = eff(t, task, "self", "exp")
        dself_c = eff(cf, task, "self", "exp")
        row = [f"{task:3s} self alone T {ds:+6.2f} (conflict-set self {dself_c:+6.2f})"]
        for x, own in (("other", "self+other"), ("world", "self+world"), ("told", "self+told")):
            dx = eff(t, task, x, "exp")
            row.append(f"{x}: alone {dx:+5.2f} pred {dself_c - dx:+6.2f} obs {eff(cf, task, own, 'exp'):+6.2f}")
        print(" | ".join(row))
