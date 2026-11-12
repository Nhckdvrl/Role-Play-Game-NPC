"""Identity slice: weight of occupation (category) vs own experience (individuating) in K and decisions.
Effects in logit units (log p_pos/p_neg, clipped at +-15) and on the probability scale; bootstrap CI over families.
occ_vs_exp: positive = the occupation wins, negative = the experience wins.
usage: analyze_identity.py RUN.jsonl [...]   (SPLIT env: dev / test / all; default all, also printed per split)"""
import json, math, random, sys
from collections import defaultdict
meta = {}
for l in open("/home/xiang/rp_mech/identity/data/prompts.jsonl"):
    r = json.loads(l); r.pop("messages"); meta[r["id"]] = r
COLS = [("self", "occ"), ("self", "exp"), ("self", "stated"), ("other", "occ"), ("other", "exp"), ("self", "occ_vs_exp"), ("self", "occ_and_exp")]

def boot(xs):
    rng = random.Random(0); m = sum(xs) / len(xs)
    b = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(2000))
    return f"{m:+.2f} [{b[50]:+.2f},{b[1949]:+.2f}]"

for run in sys.argv[1:]:
    L, Pp = defaultdict(list), defaultdict(list)
    for l in open(run):
        o = json.loads(l); m = meta.get(o["id"])
        if m is None:
            continue
        a, b = (o["lpA"], o["lpB"]) if m["pos_letter"] == "A" else (o["lpB"], o["lpA"])
        task = "K" if m["mode"] == "K" else "dec"
        k = (task, m["split"], m["fmt"], m["mode"], m["conv"], m["family"], m["valence"], m["owner"], m["form"])
        L[k].append(max(min(a - b, 15), -15)); Pp[k].append(1 / (1 + math.exp(-(a - b))))
    print(f"\n######## {run.split('/')[-1]}")
    for scale, D in (("logit", L), ("prob", Pp)):
        c = {k: sum(v) / len(v) for k, v in D.items()}
        print(f"--- {scale}")
        print(f"{'subset':14s} " + " ".join(f"{o + '/' + f:>20s}" for o, f in COLS))
        for split in ("all", "dev", "test"):
            for task in ("K", "dec"):
                fams = sorted({k[5] for k in c if split == "all" or k[1] == split})
                cells = []
                for o, f in COLS:
                    per = []
                    for fa in fams:
                        v = [c[k] - c[k[:6] + ("neg", o, f)] for k in c if k[0] == task and k[5] == fa and k[6] == "pos" and k[7] == o and k[8] == f]
                        if v:
                            per.append(sum(v) / len(v))
                    cells.append(boot(per) if per else "n/a")
                print(f"{split + ' ' + task:14s} " + " ".join(f"{x:>20s}" for x in cells))
