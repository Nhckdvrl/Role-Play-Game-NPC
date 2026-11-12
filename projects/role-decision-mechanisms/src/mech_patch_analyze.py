"""Summarise mech_patch.py output.

form : restoration = (sens_patched - sens_exp) / (sens_stated - sens_exp), where sens = LD(pos) - LD(neg),
       aggregated as a ratio of means over (family, cost, order) units.
own / world : transferred fraction = (LD_base - LD_patched) / (LD_base - LD_source), ratio of means.

usage: mech_patch_analyze.py PATCH.jsonl
"""
import json
import sys
from collections import defaultdict

rows = [json.loads(l) for l in open(sys.argv[1])]
keys = list(rows[0]["patched"].keys())
spans = ["last", "tail"]
layers = sorted({int(k[4:]) for k in keys})

units = defaultdict(dict)
for r in rows:
    fam, _, _, _, conv, _, _, order = r["base"].split("|")
    units[(r["ptype"], fam, conv, order)][r["valence"]] = r

print("n pairs:", len(rows))
# form
num = defaultdict(float)
den = 0.0
exp_s = st_s = 0.0
n = 0
for (pt, *_), u in units.items():
    if pt != "form" or len(u) < 2:
        continue
    p, q = u["pos"], u["neg"]
    se = p["base_ld"] - q["base_ld"]
    ss = p["src_ld"] - q["src_ld"]
    exp_s += se
    st_s += ss
    n += 1
    for k in keys:
        num[k] += (p["patched"][k] - q["patched"][k]) - se
    den += ss - se
print(f"\nFORM  (exp -> stated): mean sens exp {exp_s/n:+.2f}, stated {st_s/n:+.2f} (logit units), units {n}")
print("layer  " + "  ".join(f"{s:>6s}" for s in spans))
for l in layers:
    print(f"{l:5d}  " + "  ".join(f"{num[f'{s}{l}']/den:+6.2f}" for s in spans))

for pt in ("own", "world"):
    num = defaultdict(float)
    den = 0.0
    n = 0
    for (t, *_), u in units.items():
        if t != pt:
            continue
        r = u["pos"]
        den += r["base_ld"] - r["src_ld"]
        n += 1
        for k in keys:
            num[k] += r["base_ld"] - r["patched"][k]
    print(f"\n{pt.upper()} (pos -> neg): mean effect {den/n:+.2f} logits, units {n}")
    print("layer  " + "  ".join(f"{s:>6s}" for s in spans))
    for l in layers:
        print(f"{l:5d}  " + "  ".join(f"{num[f'{s}{l}']/den:+6.2f}" for s in spans))
