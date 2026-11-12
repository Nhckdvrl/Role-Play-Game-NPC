"""Ownership probe analysis: train a 'role holds this' direction (self vs other) on half of the families,
test AUC on the other half for self vs other, self vs world, told_line vs other, told_orig vs other.

usage: mech_owner_analyze.py OUT_PREFIX
"""
import json
import sys

import numpy as np

pref = sys.argv[1]
meta = [json.loads(l) for l in open(f"{pref}_meta.jsonl")]
fams = sorted({m["family"] for m in meta})
folds = [set(fams[0::2]), set(fams[1::2])]
kind = np.array([m["kind"] for m in meta])
famv = np.array([m["family"] for m in meta])


def auc(p, q):
    v = np.concatenate([p, q]); r = v.argsort().argsort() + 1
    return (r[:len(p)].sum() - len(p) * (len(p) + 1) / 2) / (len(p) * len(q))


tests = [("self", "other"), ("self", "world"), ("told_line", "other"), ("told_orig", "other"), ("self", "told_orig")]
for rep in ("last", "mean"):
    X = np.load(f"{pref}_{rep}.npy", mmap_mode="r")
    print(f"\n=== representation: {rep} token(s) of the memory sentence; direction = self vs other (held-out families); AUC")
    print("layer " + " ".join(f"{a + '>' + b:>18s}" for a, b in tests))
    for l in range(0, X.shape[1], 4):
        Xl = np.asarray(X[:, l, :], dtype=np.float32)
        res = {t: [] for t in tests}
        for k in range(2):
            tr = np.isin(famv, list(folds[k]))
            w = Xl[tr & (kind == "self")].mean(0) - Xl[tr & (kind == "other")].mean(0)
            te = ~tr
            for a, b in tests:
                pa, pb = Xl[te & (kind == a)] @ w, Xl[te & (kind == b)] @ w
                if len(pa) and len(pb):
                    res[(a, b)].append(auc(pa, pb))
        print(f"{l:5d} " + " ".join(f"{np.mean(res[t]):18.2f}" if res[t] else f"{'-':>18s}" for t in tests))
