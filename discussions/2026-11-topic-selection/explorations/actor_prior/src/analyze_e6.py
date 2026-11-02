"""E6: 2x2 traits (T+/T-) x stated value (V+/V-) on the same dilemmas. Metric = P(antisocial option B).

Symmetric 'follow the traits' predicts: T+V- drops below V- by as much as T-V+ rises above V+.
'Prosocial tie-break' predicts: a large drop for T+V- but little rise for T-V+.
"""
import collections
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path.home() / "rp_prior"
exp = sys.argv[1] if len(sys.argv) > 1 else "e6"
prompts = {r["id"]: r for r in map(json.loads, open(ROOT / f"data/{exp}_prompts.jsonl"))}
CONDS = ["V-", "V+", "T+", "T-", "T+V-", "T-V-", "T+V+", "T-V+"]


def main():
    for f in sorted((ROOT / f"runs/{exp}").glob("*.jsonl")):
        cells = collections.defaultdict(list)
        for g in map(json.loads, open(f)):
            p = prompts[g["id"]]
            a = math.exp(g["lpA"]) if g["lpA"] > -1e9 else 0.0
            b = math.exp(g["lpB"]) if g["lpB"] > -1e9 else 0.0
            if a + b == 0:
                continue
            pa = a / (a + b)
            cells[(p["pid"], p["diff"], p["cond"])].append(pa if p["role_letter"] == "A" else 1 - pa)
        c = {k: np.mean(v) for k, v in cells.items() if len(v) == 2}
        items = sorted({(k[0], k[1]) for k in c})
        m = {cd: np.mean([c[(*i, cd)] for i in items if (*i, cd) in c]) for cd in CONDS}
        print(f"{f.stem:14s} " + " ".join(f"{cd}:{m[cd]:.2f}" for cd in CONDS))
        # paired item-level shifts with bootstrap CI
        def shift(a, b):
            d = np.array([c[(*i, a)] - c[(*i, b)] for i in items if (*i, a) in c and (*i, b) in c])
            rng = np.random.default_rng(0)
            bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(1000)]
            return f"{d.mean():+.3f} [{np.percentile(bs, 2.5):+.3f},{np.percentile(bs, 97.5):+.3f}]"
        print(" " * 15 + f"prosocial traits pull antisocial value down: T+V- minus V- = {shift('T+V-', 'V-')}")
        print(" " * 15 + f"antisocial traits pull prosocial value up:  T-V+ minus V+ = {shift('T-V+', 'V+')}")
        print(" " * 15 + f"traits alone: T- minus T+ = {shift('T-', 'T+')} ; coherent T-V- minus V- = {shift('T-V-', 'V-')}")


if __name__ == "__main__":
    main()
