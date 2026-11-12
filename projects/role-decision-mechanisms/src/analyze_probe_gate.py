"""Sens (logit units) by owner/form, base vs probe-gated; also the mean fraction of context lines gated.
usage: analyze_probe_gate.py GATE.jsonl [FMT ...]   (FMT filter optional; rows without 'fmt' count as 'card')"""
import json, sys
from collections import defaultdict
rows = [json.loads(l) for l in open(sys.argv[1])]
fmts = set(sys.argv[2:]) or None
cells = defaultdict(dict)
frac = defaultdict(list)
for r in rows:
    ft = r.get("fmt", "card")
    if fmts and ft not in fmts:
        continue
    cells[(r["owner"], r["form"], r["family"], r.get("conv", "na"), r["pos_letter"], ft)][r["valence"]] = r["res"]
    frac[(r["owner"], r["form"])].append(sum(s < 0 for s in r["judged"]) / max(1, len(r["judged"])))
keys = sorted({(o, f) for (o, f, *_) in cells if o != "none"})
print(sys.argv[1].split("/")[-1], "formats:", sorted(fmts) if fmts else "all")
print(f"{'cond':16s} {'base':>7s} {'gated':>7s} {'frac lines gated':>17s}")
for o, f in keys:
    v = [c for (oo, ff, *_), c in cells.items() if oo == o and ff == f and len(c) == 2]
    b = sum(c["pos"]["base"] - c["neg"]["base"] for c in v) / len(v)
    g = sum(c["pos"]["judge_win"] - c["neg"]["judge_win"] for c in v) / len(v)
    print(f"{o + '/' + f:16s} {b:+7.2f} {g:+7.2f} {sum(frac[(o, f)]) / len(frac[(o, f)]):17.2f}")
