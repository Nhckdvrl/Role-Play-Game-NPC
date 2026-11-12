"""Summarise mech_steer.py.

For self/exp and self/stated: sens = mean over (family, cost, order) of LD(pos) - LD(neg), unsteered and steered
(steering pushes toward the role's attitude). gap_closed = (sens_exp_steered - sens_exp) / (sens_stated - sens_exp).
For none: mean shift of LD when adding +direction (raw effect of one stated-sized push).

usage: mech_steer_analyze.py STEER.jsonl
"""
import json
import sys
from collections import defaultdict

rows = [json.loads(l) for l in open(sys.argv[1])]
keys = [k for k in rows[0]["res"] if k != "base"]
cells = defaultdict(dict)
for r in rows:
    cells[(r["owner"], r["form"], r["family"], r["conv"], r["pos_letter"])][r["valence"]] = r["res"]


def sens(owner, form, key):
    vals = [c["pos"][key] - c["neg"][key] for (o, f, *_), c in cells.items() if o == owner and f == form and "pos" in c and "neg" in c]
    return sum(vals) / len(vals)


def shift_none(key):
    vals = [c["none"][key] - c["none"]["base"] for (o, *_), c in cells.items() if o == "none"]
    return sum(vals) / len(vals)


se, ss = sens("self", "exp", "base"), sens("self", "stated", "base")
print(f"unsteered sens: exp {se:+.2f}  stated {ss:+.2f}  (logits)")
print(f"{'setting':16s} {'exp sens':>9s} {'gap closed':>10s} {'stated sens':>11s} {'none shift':>10s}")
for k in sorted(keys, key=lambda x: (x.split('_')[1], x.split('_')[2], x.split('_')[0])):
    e = sens("self", "exp", k)
    s = sens("self", "stated", k)
    print(f"{k:16s} {e:+9.2f} {(e - se) / (ss - se):+10.2f} {s:+11.2f} {shift_none(k):+10.2f}")
