"""Summarise mech_srcsteer.py: decision sens (LD pos - LD neg) under source steering, per condition.

usage: mech_srcsteer_analyze.py SRCSTEER.jsonl
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


ss = sens("self", "stated", "base")
print(f"{'setting':22s} {'self stated':>11s} {'self exp':>9s} {'world exp':>9s}   (exp and world also as fraction of unsteered stated)")
for k in ["base"] + sorted([k for k in keys if k != "base"]):
    a, b, c = sens("self", "stated", k), sens("self", "exp", k), sens("world", "exp", k)
    print(f"{k:22s} {a:+11.2f} {b:+9.2f} {c:+9.2f}   exp {b/ss:+.2f}  world {c/ss:+.2f}")
