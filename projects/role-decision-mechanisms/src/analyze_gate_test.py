"""T-set gating: sens (logit units) by owner/form, overall and per format, for base vs judge-gated.
usage: analyze_gate_test.py GATE_T.jsonl"""
import json, sys
from collections import defaultdict
rows = [json.loads(l) for l in open(sys.argv[1])]
cells = defaultdict(dict)
for r in rows:
    cells[(r["fmt"], r["owner"], r["form"], r["family"], r["conv"], r["pos_letter"])][r["valence"]] = r["res"]
import os
cols = [tuple(x.split("/")) for x in os.environ.get("COLS", "self/stated,self/exp,told/exp,other/exp,other/stated,world/exp").split(",")]
def sens(fmts, o, f, k):
    v = [c["pos"][k] - c["neg"][k] for (ft, oo, ff, *_), c in cells.items() if ft in fmts and oo == o and ff == f and len(c) == 2]
    return sum(v) / len(v) if v else float("nan")
gated = sum(r["n_judge_rm"] > 0 for r in rows) / len(rows)
print(f"{sys.argv[1].split('/')[-1]}: rows with >=1 gated segment: {gated:.2f}")
print(f"{'subset':14s} " + " ".join(f"{o + '/' + f:>13s}" for o, f in cols))
FMTS = tuple(__import__("os").environ.get("FMTS", "card,json,prose").split(","))
for name, fmts in [("ALL", FMTS)] + [(x, (x,)) for x in FMTS]:
    for k in ("base", "judge_win"):
        print(f"{name + ' ' + k:14s} " + " ".join(f"{sens(fmts, o, f, k):+13.2f}" for o, f in cols))
