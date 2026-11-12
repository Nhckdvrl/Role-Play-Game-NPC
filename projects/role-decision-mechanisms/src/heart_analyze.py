"""HEART accuracy per condition (argmax over A-D, averaged over the two option rotations; per-question bootstrap CI).
usage: heart_analyze.py PROMPTS1.jsonl[,PROMPTS2.jsonl] RUN1.jsonl[,RUN2.jsonl] TAG"""
import json, math, random, sys
from collections import defaultdict
meta = {}
for p in sys.argv[1].split(","):
    for l in open(p):
        r = json.loads(l); r.pop("messages"); meta[r["id"]] = r
acc = defaultdict(lambda: defaultdict(list))
for p in sys.argv[2].split(","):
    for l in open(p):
        o = json.loads(l); m = meta[o["id"]]
        lp = {k: o.get(f"lp{k}", -math.inf) for k in "ABCD"}
        pred = max(lp, key=lp.get)
        acc[m["cond"]][m["qid"]].append(1.0 if pred == m["correct"] else 0.0)
order = ["nomem", "mem_sheet", "mem_selfbridge", "profile_sheet", "profile_bridge"]
print(f"{sys.argv[3]}")
for c in order:
    if c not in acc: continue
    xs = [sum(v) / len(v) for v in acc[c].values()]
    rng = random.Random(0); bs = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(2000))
    print(f"  {c:16s} acc {sum(xs)/len(xs):.3f} [{bs[50]:.3f},{bs[1949]:.3f}]  n={len(xs)}")
