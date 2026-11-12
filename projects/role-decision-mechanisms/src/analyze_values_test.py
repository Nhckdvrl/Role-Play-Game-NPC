"""Held-out value slice (VT): K and decision sens by owner/form, overall and per format; bootstrap CI over 12 families.
usage: analyze_values_test.py RUN.jsonl [...]"""
import json, math, random, sys
from collections import defaultdict
meta = {}
for l in open("/home/xiang/rp_mech/values_test/prompts.jsonl"):
    r = json.loads(l); r.pop("messages"); meta[r["id"]] = r
cols = [("self", "stated"), ("self", "exp"), ("told", "exp"), ("other", "stated"), ("other", "exp"), ("world", "exp")]
def boot(xs):
    rng = random.Random(0); m = sum(xs) / len(xs)
    b = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(2000)); return f"{m:+.2f} [{b[50]:+.2f},{b[1949]:+.2f}]"
for run in sys.argv[1:]:
    acc = defaultdict(list)
    for l in open(run):
        o = json.loads(l); m = meta.get(o["id"])
        if m is None: continue
        pa, pb = math.exp(o["lpA"]), math.exp(o["lpB"])
        if pa + pb == 0: continue
        task = "K" if m["mode"] == "K" else "dec"
        acc[(task, m["fmt"], m["family"], m["valence"], m["owner"], m["form"])].append((pa if m["pos_letter"] == "A" else pb) / (pa + pb))
    c = {k: sum(v) / len(v) for k, v in acc.items()}
    fams = sorted({k[2] for k in c})
    print(f"\n######## {run.split('/')[-1]}  (VT: 12 held-out value families)")
    print(f"{'subset':12s} " + " ".join(f"{o + '/' + f:>20s}" for o, f in cols))
    for name, fmts in (("ALL", ("card", "json", "prose")), ("card", ("card",)), ("json", ("json",)), ("prose", ("prose",))):
        for task in ("K", "dec"):
            cells = []
            for o, f in cols:
                per = []
                for fa in fams:
                    v = [c[(task, ft, fa, "pos", o, f)] - c[(task, ft, fa, "neg", o, f)] for ft in fmts if (task, ft, fa, "pos", o, f) in c]
                    if v: per.append(sum(v) / len(v))
                cells.append(boot(per) if per else "n/a")
            print(f"{name + ' ' + task:12s} " + " ".join(f"{x:>20s}" for x in cells))
