"""LifeChoice accuracy: per item, letter probabilities (normalised over A-D) are mapped back to option identity and
averaged over the two option orders; accuracy = argmax == gold. Bootstrap CI over items; paired base-vs-SFT difference.
usage: analyze_lifechoice.py"""
import json, math, os, random
from collections import defaultdict
meta = {}
import glob
for pf in ["/home/xiang/rp_mech/lifechoice/prompts.jsonl"] + glob.glob("/home/xiang/rp_mech/lifechoice/kfirst_*.jsonl"):
    if "kfirst_pre" in pf: continue
    for l in open(pf):
        r = json.loads(l); r.pop("messages"); meta[r["id"]] = r

def load(path):
    acc = defaultdict(lambda: [0.0] * 4)
    for l in open(path):
        o = json.loads(l); m = meta[o["id"]]
        lp = [max(o[f"lp{x}"], -50) for x in "ABCD"]
        z = sum(math.exp(v) for v in lp) or 1.0
        for pos, opt in enumerate(m["perm"]):
            acc[(m["item"], m["cond"])][opt] += math.exp(lp[pos]) / z / 2
    return {k: int(max(range(4), key=lambda i: v[i]) == meta[f"{k[0]}|{k[1]}|orig"]["gold"]) for k, v in acc.items()}

def ci(xs):
    rng = random.Random(0); n = len(xs); m = sum(xs) / n
    b = sorted(sum(xs[rng.randrange(n)] for _ in range(n)) / n for _ in range(1000))
    return f"{m:.3f} [{b[25]:.3f},{b[974]:.3f}]"

for tag in ("qwen3_8b", "llama31_8b", "gemma3_12b", "mistral24b"):
    res = {}
    for v in ("base", "sft", "kfirst"):
        p = f"/home/xiang/rp_mech/lifechoice/runs/{v}_{tag}.jsonl"
        if os.path.exists(p) and os.path.getsize(p) > 0:
            res[v] = load(p)
    if not res:
        continue
    line = [f"{tag:12s}"]
    for v, R in res.items():
        for cond in ("full", "nomem", "kfirst"):
            xs = [R[k] for k in R if k[1] == cond]
            if xs:
                line.append(f"{v} {cond} {ci(xs)}")
    if "base" in res and "sft" in res:
        items = [k for k in res["base"] if k[1] == "full" and k in res["sft"]]
        line.append(f"SFT-base (full) {ci([res['sft'][k] - res['base'][k] for k in items])}")
    if "base" in res and "kfirst" in res:
        items = [k for k in res["base"] if k[1] == "full" and (k[0], "kfirst") in res["kfirst"]]
        line.append(f"Kfirst-base {ci([res['kfirst'][(k[0], 'kfirst')] - res['base'][k] for k in items])}")
    print("  ".join(line))

# (a) model-specific story-dependent subset: items the BASE model gets wrong without the story. Biased toward any
#     condition other than base-full (regression to the mean), so only descriptive.
# (b) model-independent subset: items that at least 3 of the 4 BASE models get wrong without the story.
print("\nstory-dependent subset (base nomem wrong):")
for tag in ("qwen3_8b", "llama31_8b", "gemma3_12b", "mistral24b"):
    res = {}
    for v in ("base", "sft", "kfirst"):
        p = f"/home/xiang/rp_mech/lifechoice/runs/{v}_{tag}.jsonl"
        if os.path.exists(p) and os.path.getsize(p) > 0:
            res[v] = load(p)
    if "base" not in res:
        continue
    hard = [k[0] for k in res["base"] if k[1] == "nomem" and res["base"][k] == 0]
    line = [f"{tag:12s} n={len(hard)}"]
    line.append(f"base full {ci([res['base'][(i, 'full')] for i in hard])}")
    if "sft" in res:
        line.append(f"sft full {ci([res['sft'][(i, 'full')] for i in hard if (i, 'full') in res['sft']])}")
    if "kfirst" in res:
        line.append(f"kfirst {ci([res['kfirst'][(i, 'kfirst')] for i in hard if (i, 'kfirst') in res['kfirst']])}")
    print("  ".join(line))

allb = {}
for tag in ("qwen3_8b", "llama31_8b", "gemma3_12b", "mistral24b"):
    p = f"/home/xiang/rp_mech/lifechoice/runs/base_{tag}.jsonl"
    if os.path.exists(p) and os.path.getsize(p) > 0:
        allb[tag] = load(p)
if len(allb) == 4:
    items = {k[0] for k in allb["qwen3_8b"] if k[1] == "nomem"}
    common = [i for i in items if sum(allb[t].get((i, "nomem"), 1) == 0 for t in allb) >= 3]
    print(f"\nmodel-independent story-dependent subset (>=3/4 base models wrong without story): n={len(common)}")
    for tag in allb:
        line = [f"{tag:12s}"]
        for v in ("base", "sft", "kfirst"):
            p = f"/home/xiang/rp_mech/lifechoice/runs/{v}_{tag}.jsonl"
            if not (os.path.exists(p) and os.path.getsize(p) > 0):
                continue
            R = allb[tag] if v == "base" else load(p)
            cond = "kfirst" if v == "kfirst" else "full"
            xs = [R[(i, cond)] for i in common if (i, cond) in R]
            line.append(f"{v} {ci(xs)}")
        print("  ".join(line))
