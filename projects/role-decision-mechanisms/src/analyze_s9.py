"""S9: event vs precedent experiences. usage: analyze_s9.py PROMPTS RUN1 [RUN2 ...]"""
import random, sys
from analyze_s2 import Q, load
def boot(xs, n=2000):
    rng = random.Random(0); m = sum(xs) / len(xs)
    bs = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(n)); return f"{m:+.2f} [{bs[50]:+.2f},{bs[1949]:+.2f}]"
for run in sys.argv[2:]:
    cells, kind, bad = load(sys.argv[1], run); q = Q(cells); fams = sorted(kind)
    print(f"\n######## {run.split('/')[-1]}")
    print(f"{'task':4s} {'form':5s} {'self':>20s} {'other':>20s} {'world':>20s}   other/self")
    for mode, modes in (("K", ["K"]), ("dec", ["P", "EU"])):
        for f in ("exp", "prec"):
            vals = {o: [sum(q.sens(fa, o, f, m) for m in modes) / len(modes) for fa in fams] for o in ("self", "other", "world")}
            r = (sum(vals["other"]) / len(fams)) / (sum(vals["self"]) / len(fams))
            print(f"{mode:4s} {f:5s} " + " ".join(f"{boot(vals[o]):>20s}" for o in ("self", "other", "world")) + f"   {r:+.2f}")
