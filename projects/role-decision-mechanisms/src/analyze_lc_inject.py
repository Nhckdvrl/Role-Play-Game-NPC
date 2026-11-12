"""Natural-context injection: shift of P(target option) caused by one injected sentence, by source and position.
P over A-D, mapped to option identity, averaged over 2 orders. shift = P(X|inject) - P(X|none). Bootstrap over items.
usage: analyze_lc_inject.py"""
import json, math, os, random
from collections import defaultdict
meta = {}
for l in open("/home/xiang/rp_mech/lc_inject/prompts.jsonl"):
    r = json.loads(l); r.pop("messages"); meta[r["id"]] = r
def ci(xs):
    rng = random.Random(0); n = len(xs); m = sum(xs) / n
    b = sorted(sum(xs[rng.randrange(n)] for _ in range(n)) / n for _ in range(1000))
    return f"{m:+.3f} [{b[25]:+.3f},{b[974]:+.3f}]"
import sys
PRE = sys.argv[1] if len(sys.argv) > 1 else ""  # "" (base) or "sft_"
for tag in ("qwen3_8b", "llama31_8b", "gemma3_12b", "mistral24b"):
    p = f"/home/xiang/rp_mech/lc_inject/runs/{PRE}{tag}.jsonl"
    if not (os.path.exists(p) and os.path.getsize(p) > 0):
        continue
    P = defaultdict(float)
    for l in open(p):
        o = json.loads(l); m = meta[o["id"]]
        lp = [max(o[f"lp{x}"], -50) for x in "ABCD"]; z = sum(math.exp(v) for v in lp) or 1.0
        pos_of_target = m["perm"].index(m["target"])
        P[(m["item"], m["src"], m["pos"])] += math.exp(lp[pos_of_target]) / z / 2
    items = sorted({k[0] for k in P})
    base = [P[(i, "none", "none")] for i in items]
    print(f"\n## {PRE}{tag}  items={len(items)}  P(target) without injection = {sum(base) / len(base):.3f}")
    res = {}
    for pos in ("near", "far"):
        row = []
        for src in ("self", "other", "world"):
            d = [P[(i, src, pos)] - P[(i, "none", "none")] for i in items]
            res[(src, pos)] = sum(d) / len(d)
            row.append(f"{src} {ci(d)}")
        print(f"{pos:5s} " + "  ".join(row) + f"   other/self {res[('other', pos)] / res[('self', pos)]:.2f}  world/self {res[('world', pos)] / res[('self', pos)]:.2f}")
