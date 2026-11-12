"""Analyse S8 (values slice). sens = p_pos(pos) - p_pos(neg), per family, bootstrap CI over families.

usage: analyze_s8.py PROMPTS.jsonl RUN1.jsonl [RUN2 ...]
"""
import json
import math
import random
import sys
from collections import defaultdict


def boot(xs, n=2000):
    rng = random.Random(0)
    m = sum(xs) / len(xs)
    bs = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(n))
    return f"{m:+.2f} [{bs[50]:+.2f},{bs[1949]:+.2f}]"


meta = {}
for l in open(sys.argv[1]):
    r = json.loads(l)
    r.pop("messages")
    meta[r["id"]] = r
for run in sys.argv[2:]:
    acc = defaultdict(list)
    for l in open(run):
        o = json.loads(l)
        m = meta[o["id"]]
        pa, pb = math.exp(o["lpA"]), math.exp(o["lpB"])
        if pa + pb == 0:
            continue
        acc[(m["iv"], m["mode"], m["family"], m["valence"], m["owner"], m["form"])].append((pa if m["pos_letter"] == "A" else pb) / (pa + pb))
    c = {k: sum(v) / len(v) for k, v in acc.items()}
    fams = sorted({k[2] for k in c})
    print(f"\n######## {run.split('/')[-1]}")
    print(f"{'iv/mode':16s} {'self stated':>20s} {'self exp':>20s} {'other exp':>20s} {'other stated':>20s} {'world exp':>20s}  none p_pos")

    def sens(iv, modes, o, f, fam):
        return sum(c[(iv, md, fam, "pos", o, f)] - c[(iv, md, fam, "neg", o, f)] for md in modes) / len(modes)
    for iv, modes in (("plain", ["K"]), ("plain", ["P", "EU"]), ("bridge_stmt", ["P", "EU"])):
        cells = [boot([sens(iv, modes, o, f, fam) for fam in fams]) for o, f in (("self", "stated"), ("self", "exp"), ("other", "exp"), ("other", "stated"), ("world", "exp"))]
        dn = sum(c[(iv, md, fam, "none", "none", "none")] for md in modes for fam in fams) / (len(modes) * len(fams))
        print(f"{iv + '/' + '+'.join(modes):16s} " + " ".join(f"{x:>20s}" for x in cells) + f"  {dn:.2f}")
