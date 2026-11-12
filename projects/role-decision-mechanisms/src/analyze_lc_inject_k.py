"""K for the natural-context injection: P(Yes) to "Does <name> know that someone once chose X ...?" by source/position;
K leak ratio = (P(Yes|src) - P(Yes|none)) / (P(Yes|self) - P(Yes|none)); compared with the decision ratio from E3.
usage: analyze_lc_inject_k.py"""
import json, math, os, random
from collections import defaultdict
meta = {}
for l in open("/home/xiang/rp_mech/lc_inject/k_prompts.jsonl"):
    r = json.loads(l); r.pop("messages"); meta[r["id"]] = r
for tag in ("qwen3_8b", "llama31_8b", "gemma3_12b", "mistral24b"):
    p = f"/home/xiang/rp_mech/lc_inject/runs/k_{tag}.jsonl"
    if not (os.path.exists(p) and os.path.getsize(p) > 0):
        continue
    Y, mass = defaultdict(list), []
    for l in open(p):
        o = json.loads(l); m = meta[o["id"]]
        pa, pb = math.exp(o["lpA"]), math.exp(o["lpB"]); mass.append(pa + pb)
        if pa + pb == 0: continue
        Y[(m["item"], m["src"], m["pos"])].append((pa if m["yes_letter"] == "A" else pb) / (pa + pb))
    c = {k: sum(v) / len(v) for k, v in Y.items()}
    items = sorted({k[0] for k in c})
    none = sum(c[(i, "none", "none")] for i in items) / len(items)
    print(f"\n## {tag}  A+B mass {sum(mass) / len(mass):.2f}  P(Yes) none = {none:.2f}")
    for pos in ("near", "far"):
        v = {s: sum(c[(i, s, pos)] for i in items) / len(items) for s in ("self", "other", "world")}
        d = {s: v[s] - none for s in v}
        print(f"{pos:5s} P(Yes): self {v['self']:.2f} other {v['other']:.2f} world {v['world']:.2f}   K leak ratio: other {d['other'] / d['self']:.2f} world {d['world'] / d['self']:.2f}")
