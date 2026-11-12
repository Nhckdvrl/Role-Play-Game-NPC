"""S12 analysis: attitude effect (P,EU; both costs) per sheet variant x placement x form.
usage: analyze_s12.py PROMPTS RUN1 [RUN2 ...]"""
import json, math, random, sys
from collections import defaultdict
meta = {}
for l in open(sys.argv[1]):
    r = json.loads(l); r.pop("messages"); meta[r["id"]] = r
def boot(xs):
    rng = random.Random(0); m = sum(xs) / len(xs); bs = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(2000)); return f"{m:+.2f} [{bs[50]:+.2f},{bs[1949]:+.2f}]"
for run in sys.argv[2:]:
    acc = defaultdict(list)
    for l in open(run):
        o = json.loads(l); m = meta[o["id"]]; pa, pb = math.exp(o["lpA"]), math.exp(o["lpB"])
        acc[(m["iv"], m["family"], m["valence"], m["form"])].append((pa if m["pos_letter"] == "A" else pb) / (pa + pb))
    c = {k: sum(v) / len(v) for k, v in acc.items()}; fams = sorted({k[1] for k in c})
    print(f"\n######## {run.split('/')[-1]}")
    print(f"{'form':7s} {'full sheet':>20s} {'full bridge':>20s} {'bare sheet':>20s} {'bare bridge':>20s}")
    for f in ("stated", "exp"):
        cells = [boot([c[(iv, fa, "pos", f)] - c[(iv, fa, "neg", f)] for fa in fams]) for iv in ("full_sheet", "full_bridge", "bare_sheet", "bare_bridge")]
        print(f"{f:7s} " + " ".join(f"{x:>20s}" for x in cells))
