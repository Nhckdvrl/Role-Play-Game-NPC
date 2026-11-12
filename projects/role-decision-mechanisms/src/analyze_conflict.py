"""T-conflict: own experience vs opposite inaccessible (other / world) or legitimately told evidence.

sens(owner) = p_pos(own pos) - p_pos(own neg), decisions = P + EU averaged over costs; K separately.
retained = sens(self+X) / sens(self): 1.0 means the opposite evidence is ignored.
95% bootstrap CI over the 18 families (retained: ratio of means within each bootstrap sample).

usage: analyze_conflict.py RUN.jsonl [...]   (PROMPTS env overrides the prompt file)
"""
import json
import math
import os
import random
import sys
from collections import defaultdict

P = os.environ.get("PROMPTS", "/home/xiang/rp_mech/test_conf/data/prompts.jsonl")
meta = {}
for l in open(P):
    r = json.loads(l)
    r.pop("messages")
    meta[r["id"]] = r
OWN = ["self", "self+other", "self+world", "self+told"]

for run in sys.argv[1:]:
    acc = defaultdict(list)
    for l in open(run):
        o = json.loads(l)
        m = meta[o["id"]]
        pa, pb = math.exp(o["lpA"]), math.exp(o["lpB"])
        if pa + pb == 0:
            continue
        acc[(m["fmt"], m["mode"], m["conv"], m["family"], m["valence"], m["owner"])].append((pa if m["pos_letter"] == "A" else pb) / (pa + pb))
    c = {k: sum(v) / len(v) for k, v in acc.items()}
    fams = sorted({k[3] for k in c})
    fmts_all = sorted({k[0] for k in c})

    def sens(fmts, modes, o, fam):
        v = [c[(ft, md, cv, fam, "pos", o)] - c[(ft, md, cv, fam, "neg", o)] for ft in fmts for md in modes
             for cv in (("na",) if md == "K" else ("pos_costly", "neg_costly")) if (ft, md, cv, fam, "pos", o) in c]
        return sum(v) / len(v)

    print(f"\n######## {run.split('/')[-1]}")
    print(f"{'subset':12s} " + " ".join(f"{o:>13s}" for o in OWN) + "   retained: " + " ".join(f"{o:>20s}" for o in OWN[1:]))
    for name, fmts in [("ALL", fmts_all)] + [(x, [x]) for x in fmts_all]:
        for task, modes in (("K", ["K"]), ("dec", ["P", "EU"])):
            per = {o: [sens(fmts, modes, o, fa) for fa in fams] for o in OWN}
            rng = random.Random(0)
            rets = {o: [] for o in OWN[1:]}
            for _ in range(2000):
                idx = [rng.randrange(len(fams)) for _ in fams]
                base = sum(per["self"][i] for i in idx)
                for o in OWN[1:]:
                    rets[o].append(sum(per[o][i] for i in idx) / base if abs(base) > 1e-9 else float("nan"))
            cells = []
            for o in OWN[1:]:
                b = sorted(rets[o])
                cells.append(f"{sum(per[o]) / sum(per['self']):.2f} [{b[50]:.2f},{b[1949]:.2f}]")
            print(f"{name + ' ' + task:12s} " + " ".join(f"{sum(per[o]) / len(fams):+13.2f}" for o in OWN) + "   " + " ".join(f"{x:>20s}" for x in cells))
