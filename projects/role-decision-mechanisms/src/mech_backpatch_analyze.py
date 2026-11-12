"""Back-patching: decision sens per condition for each SRC>TGT pair. usage: mech_backpatch_analyze.py BP.jsonl"""
import json, sys
from collections import defaultdict
rows = [json.loads(l) for l in open(sys.argv[1])]
keys = list(rows[0]["res"].keys())
cells = defaultdict(dict)
for r in rows:
    cells[(r["owner"], r["form"], r["family"], r["conv"], r["pos_letter"])][r["valence"]] = r["res"]
def sens(o, f, k):
    v = [c["pos"][k] - c["neg"][k] for (oo, ff, *_), c in cells.items() if oo == o and ff == f and len(c) == 2]
    return sum(v) / len(v)
def none_mean(k):
    v = [c["none"][k] for (oo, *_), c in cells.items() if oo == "none"]
    return sum(v) / len(v)
cols = [("self", "stated"), ("self", "exp"), ("other", "exp"), ("world", "exp")]
print(f"{'pair':8s} " + " ".join(f"{o + '/' + f:>12s}" for o, f in cols) + "   other/self  world/self  none mean LD")
for k in keys:
    s = [sens(o, f, k) for o, f in cols]
    print(f"{k:8s} " + " ".join(f"{x:+12.2f}" for x in s) + f"   {s[2]/s[1]:+.2f}      {s[3]/s[1]:+.2f}      {none_mean(k):+.2f}")
