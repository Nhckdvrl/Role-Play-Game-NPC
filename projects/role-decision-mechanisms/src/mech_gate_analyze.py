"""Summarise mech_gate.py: judge accuracy and decision sens under each gating variant.
usage: mech_gate_analyze.py GATE.jsonl"""
import json
import sys
from collections import defaultdict

from families import FAMILIES
from families_values import VFAMILIES

ROLE = {f["id"]: f["role"] for f in FAMILIES + VFAMILIES}
rows = [json.loads(l) for l in open(sys.argv[1])]
by = defaultdict(list)
for r in rows:
    for o, p in zip(r["owners"], r["judged"]):
        by["role's own lines" if o == ROLE[r["family"]] else ("world events" if o == "WORLD" else "other character's lines")].append(p)
print("judge: mean P(knowable) and share judged not knowable (P<0.5)")
for k, v in by.items():
    print(f"  {k:24s} P={sum(v)/len(v):.2f}  gated={sum(p < 0.5 for p in v)/len(v):.2f}  (n={len(v)})")
keys = list(rows[0]["res"].keys())
cells = defaultdict(dict)
for r in rows:
    cells[(r["owner"] + ("/" + r["form"] if r["form"] == "stated" else ""), r["family"], r["conv"], r["pos_letter"])][r["valence"]] = r["res"]


def sens(owner, key):
    v = [c["pos"][key] - c["neg"][key] for (o, *_), c in cells.items() if o == owner and len(c) == 2]
    return sum(v) / len(v)


owners = [o for o in ("self", "self/stated", "told", "other", "other/stated", "world") if any(k[0] == o for k in cells)]
print(f"\n{'variant':12s} " + " ".join(f"{o:>9s}" for o in owners) + "   (sens in logit units; 'told' should count like 'self', 'other'/'world' should not)")
for k in keys:
    print(f"{k:12s} " + " ".join(f"{sens(o, k):+9.2f}" for o in owners))
