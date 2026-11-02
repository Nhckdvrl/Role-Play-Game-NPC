"""Generic: P(role) per framing for an experiment dir. usage: analyze_frames.py EXP frame1 frame2 ..."""
import collections, json, math, sys
from pathlib import Path
import numpy as np
ROOT = Path.home() / "rp_prior"
exp, frames = sys.argv[1], sys.argv[2:]
prompts = {r["id"]: r for r in map(json.loads, open(ROOT / f"data/{exp}_prompts.jsonl"))}
for f in sorted((ROOT / f"runs/{exp}").glob("*.jsonl")):
    cells = collections.defaultdict(list)
    for g in map(json.loads, open(f)):
        p = prompts[g["id"]]
        a = math.exp(g["lpA"]) if g["lpA"] > -1e9 else 0.0
        b = math.exp(g["lpB"]) if g["lpB"] > -1e9 else 0.0
        if a + b == 0: continue
        pa = a / (a + b)
        cells[(p["pid"], p["diff"], p["cond"])].append(pa if p["role_letter"] == "A" else 1 - pa)
    c = {k: np.mean(v) for k, v in cells.items() if len(v) == 2}
    items = sorted({(k[0], k[1]) for k in c})
    res = {fr: np.mean([c[(*i, fr)] for i in items if (*i, fr) in c]) for fr in frames}
    rec = [i for i in items if c.get((*i, frames[0]), 0) > 0.5]
    cond_rate = {fr: np.mean([c[(*i, fr)] > 0.5 for i in rec if (*i, fr) in c]) for fr in frames[1:]}
    print(f"{f.stem:16s} " + "  ".join(f"{fr} {v:.3f}" for fr, v in res.items()) +
          f" | {frames[0]}-correct items {len(rec)}/{len(items)}; among them role-choice rate: " +
          ", ".join(f"{k} {v:.3f}" for k, v in cond_rate.items()))
