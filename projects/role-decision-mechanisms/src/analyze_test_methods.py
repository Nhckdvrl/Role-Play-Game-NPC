"""T set, decisions only: plain vs frozen methods (bridge_correct, selfbridge3; optional extra runs).
usage: analyze_test_methods.py TAG"""
import json, math, random, sys
from collections import defaultdict
tag = sys.argv[1]
P = "/home/xiang/rp_mech/test/data/prompts.jsonl"
meta = {}
for l in open(P):
    r = json.loads(l); r.pop("messages"); meta[r["id"]] = r
runs = {"plain": f"/home/xiang/rp_mech/test/runs/{tag}.jsonl", "bridge_correct": f"/home/xiang/rp_mech/test/methods/runs/bridge_{tag}.jsonl",
        "selfbridge3": f"/home/xiang/rp_mech/test/methods/runs/sb3_{tag}.jsonl", "sft": f"/home/xiang/rp_mech/sft/T_sft_{tag}.jsonl"}
cols = [("self", "stated"), ("self", "exp"), ("told", "exp"), ("other", "exp"), ("other", "stated"), ("world", "exp")]
def boot(xs):
    rng = random.Random(0); m = sum(xs) / len(xs); bs = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(2000)); return f"{m:+.2f} [{bs[50]:+.2f},{bs[1949]:+.2f}]"
print(f"######## {tag} (T set, decisions P+EU, averaged over costs and formats)")
print(f"{'method':15s} " + " ".join(f"{o + '/' + f:>20s}" for o, f in cols) + "   none p_pos")
for name, path in runs.items():
    try:
        acc = defaultdict(list)
        for l in open(path):
            o = json.loads(l); m = meta[o["id"]]
            if m["mode"] not in ("P", "EU"): continue
            pa, pb = math.exp(o["lpA"]), math.exp(o["lpB"])
            if pa + pb == 0: continue
            acc[(m["family"], m["valence"], m["owner"], m["form"])].append((pa if m["pos_letter"] == "A" else pb) / (pa + pb))
    except FileNotFoundError:
        continue
    c = {k: sum(v) / len(v) for k, v in acc.items()}; fams = sorted({k[0] for k in c})
    cells = [boot([c[(fa, "pos", o, f)] - c[(fa, "neg", o, f)] for fa in fams]) for o, f in cols]
    dn = sum(c[(fa, "none", "none", "none")] for fa in fams) / len(fams)
    print(f"{name:15s} " + " ".join(f"{x:>20s}" for x in cells) + f"   {dn:.2f}")
