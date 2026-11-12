"""Analyse S1 v3 prompt interventions.

Per intervention: attitude effect on decisions (P, EU pooled; averaged over cost arrangements), for
self/stated, self/exp, other/exp, world/exp; P(role-consistent | role-consistent option costly) for self/exp;
95% bootstrap CIs over families for the self/exp effect.

usage: analyze_s3.py PROMPTS.jsonl RUN1.jsonl [RUN2.jsonl ...]
"""
import json
import math
import random
import sys
from collections import defaultdict


def boot(xs, n=2000):
    rng = random.Random(0)
    m = sum(xs) / len(xs)
    bs = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(n))
    return m, bs[50], bs[1949]


for run in sys.argv[2:]:
    meta = {}
    for l in open(sys.argv[1]):
        r = json.loads(l)
        r.pop("messages")
        meta[r["id"]] = r
    acc = defaultdict(list)
    for l in open(run):
        o = json.loads(l)
        m = meta[o["id"]]
        a, b = o["lpA"], o["lpB"]
        if a == -math.inf and b == -math.inf:
            continue
        pa, pb = math.exp(a), math.exp(b)
        acc[(m["iv"], m["family"], m["valence"], m["owner"], m["form"], m["conv"])].append((pa if m["pos_letter"] == "A" else pb) / (pa + pb))
    c = {k: sum(v) / len(v) for k, v in acc.items()}
    fams = sorted({k[1] for k in c})
    print(f"\n######## {run.split('/')[-1]}")
    print(f"{'intervention':13s} {'self stated':>12s} {'self exp [95% CI]':>24s} {'other exp':>10s} {'world exp':>10s} {'none->pos':>10s}  rc|costly exp  rc|costly stated")
    for iv in sorted({k[0] for k in c}, key=lambda x: (x != "plain", x)):
        def sens(o, f, fam):
            return sum(c[(iv, fam, "pos", o, f, cv)] - c[(iv, fam, "neg", o, f, cv)] for cv in ("pos_costly", "neg_costly")) / 2
        def rc(f):
            xs = []
            for fam in fams:
                for v in ("pos", "neg"):
                    cv = "pos_costly" if v == "pos" else "neg_costly"
                    p = c[(iv, fam, v, "self", f, cv)]
                    xs.append(p if v == "pos" else 1 - p)
            return sum(xs) / len(xs)
        se = boot([sens("self", "exp", f) for f in fams])
        ss = sum(sens("self", "stated", f) for f in fams) / len(fams)
        so = sum(sens("other", "exp", f) for f in fams) / len(fams) if (iv, fams[0], "pos", "other", "exp", "pos_costly") in c else float("nan")
        sw = sum(sens("world", "exp", f) for f in fams) / len(fams)
        dn = sum(c[(iv, f, "none", "none", "none", cv)] for f in fams for cv in ("pos_costly", "neg_costly")) / (2 * len(fams))
        print(f"{iv:13s} {ss:+12.2f}   {se[0]:+.2f} [{se[1]:+.2f},{se[2]:+.2f}]   {so:+10.2f} {sw:+10.2f} {dn:10.2f}      {rc('exp'):.2f}          {rc('stated'):.2f}")
