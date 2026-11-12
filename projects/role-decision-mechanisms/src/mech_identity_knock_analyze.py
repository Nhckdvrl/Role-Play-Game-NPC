"""Summarize mech_identity_knock output: effect (LD(pos) - LD(neg), logits) per mode x form, base and after
blocking tail->span attention (all layers / each quarter). For a single-source form, 'contribution' = base - knocked.
usage: mech_identity_knock_analyze.py KNOCK.jsonl [SPLIT]"""
import json, sys
from collections import defaultdict
rows = [json.loads(l) for l in open(sys.argv[1])]
split = sys.argv[2] if len(sys.argv) > 2 else "all"
cell = defaultdict(dict)
for r in rows:
    if split != "all" and r["split"] != split:
        continue
    cell[(r["mode"], r["form"], r["family"], r["conv"], r["pos_letter"])][r["valence"]] = r["res"]
names = sorted({k for r in rows for k in r["res"]}, key=lambda x: (x != "base", x))
print(f"{sys.argv[1].split('/')[-1]}  split={split}  quarters={rows[0]['quarters']}")
for mode in ("K", "EU"):
    for form in ("occ", "exp", "occ_vs_exp"):
        cs = [c for (md, f, *_), c in cell.items() if md == mode and f == form and len(c) == 2]
        if not cs:
            continue
        eff = {n: sum(c["pos"][n] - c["neg"][n] for c in cs) / len(cs) for n in names if n in cs[0]["pos"]}
        print(f"{mode:3s} {form:11s} n={len(cs):3d} " + "  ".join(f"{n}={v:+.2f}" for n, v in eff.items()))
