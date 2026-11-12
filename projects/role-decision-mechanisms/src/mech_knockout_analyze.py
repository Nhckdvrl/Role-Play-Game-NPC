"""Summarise mech_knockout.py: decision sens (LD pos - LD neg) after blocking tail->source attention.

usage: mech_knockout_analyze.py KO.jsonl
"""
import json
import sys
from collections import defaultdict

rows = [json.loads(l) for l in open(sys.argv[1])]
keys = list(rows[0]["res"].keys())
cells = defaultdict(dict)
for r in rows:
    cells[(r["owner"], r["form"], r["family"], r["conv"], r["pos_letter"])][r["valence"]] = r["res"]


def sens(owner, form, key):
    v = [c["pos"][key] - c["neg"][key] for (o, f, *_), c in cells.items() if o == owner and f == form and len(c) == 2]
    return sum(v) / len(v)


conds = [("self", "stated"), ("self", "exp"), ("world", "exp")]
base = {c: sens(*c, "base") for c in conds}
print(f"{'knockout':16s} " + "  ".join(f"{o+' '+f:>18s}" for o, f in conds) + "    (remaining fraction of the unblocked effect)")
for k in keys:
    print(f"{k:16s} " + "  ".join(f"{sens(*c, k):+8.2f} ({sens(*c, k)/base[c]:+.2f})" for c in conds))
