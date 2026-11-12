"""Held-out T set: do the dev phenomena replicate on new families, settings and formats?

Per model: overall and per format (card / json / prose), sens = p_pos(pos) - p_pos(neg), decisions = P and EU
pooled and averaged over cost arrangements; K reported separately. 95% bootstrap CI over the 18 families.

usage: analyze_test.py RUN1.jsonl [RUN2 ...]
"""
import json
import math
import random
import sys
from collections import defaultdict

import os
P = os.environ.get("PROMPTS", "/home/xiang/rp_mech/test/data/prompts.jsonl")
FMTS = os.environ.get("FMTS", "card,json,prose").split(",")
meta = {}
for l in open(P):
    r = json.loads(l)
    r.pop("messages")
    meta[r["id"]] = r


def boot(xs):
    rng = random.Random(0)
    m = sum(xs) / len(xs)
    bs = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(2000))
    return m, bs[50], bs[1949]


def fmt(t):
    return f"{t[0]:+.2f} [{t[1]:+.2f},{t[2]:+.2f}]"


for run in sys.argv[1:]:
    acc = defaultdict(list)
    for l in open(run):
        o = json.loads(l)
        m = meta[o["id"]]
        pa, pb = math.exp(o["lpA"]), math.exp(o["lpB"])
        if pa + pb == 0:
            continue
        acc[(m["fmt"], m["mode"], m["conv"], m["family"], m["valence"], m["owner"], m["form"])].append((pa if m["pos_letter"] == "A" else pb) / (pa + pb))
    c = {k: sum(v) / len(v) for k, v in acc.items()}
    fams = sorted({k[3] for k in c})

    def sens(fmts, modes, o, f, fam):
        vals = []
        for ft in fmts:
            for md in modes:
                for cv in (("na",) if md == "K" else ("pos_costly", "neg_costly")):
                    if (ft, md, cv, fam, "pos", o, f) in c:
                        vals.append(c[(ft, md, cv, fam, "pos", o, f)] - c[(ft, md, cv, fam, "neg", o, f)])
        return sum(vals) / len(vals)

    def convw(fmts, fam):
        vals = [c[(ft, md, "neg_costly", fam, "none", "none", "none")] - c[(ft, md, "pos_costly", fam, "none", "none", "none")] for ft in fmts for md in ("P", "EU") if (ft, md, "neg_costly", fam, "none", "none", "none") in c]
        return sum(vals) / len(vals)

    print(f"\n######## {run.split('/')[-1]}  (T set: 18 held-out families)")
    cols = [("self", "stated"), ("self", "exp"), ("told", "exp"), ("other", "exp"), ("other", "stated"), ("world", "exp")]
    print(f"{'subset':14s} " + " ".join(f"{o + '/' + f:>20s}" for o, f in cols) + f" {'conv wt':>8s}")
    for name, fmts in [("ALL", FMTS)] + [(x, [x]) for x in FMTS]:
        for task, modes in (("K", ["K"]), ("dec", ["P", "EU"]), ("EU", ["EU"])):
            cells = [fmt(boot([sens(fmts, modes, o, f, fa) for fa in fams])) for o, f in cols]
            cw = "" if task == "K" else f"{sum(convw(fmts, fa) for fa in fams) / len(fams):+8.2f}"
            print(f"{name + ' ' + task:14s} " + " ".join(f"{x:>20s}" for x in cells) + f" {cw}")
