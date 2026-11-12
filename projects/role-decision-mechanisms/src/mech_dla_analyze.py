"""Analyse mech_dla.py: per-layer direct logit attribution of (pos - neg valence), attention vs MLP,
for K and decision prompts, self/exp vs world/exp (and other/exp, self/stated).
Prints the cumulative curve (sum of contributions up to layer l) and the layers with the largest
negative (cancelling) contributions.

usage: mech_dla_analyze.py DLA.npz
"""
import json
import sys

import numpy as np

z = np.load(sys.argv[1])
dla, ld, meta = z["dla"], z["ld"], json.loads(str(z["meta"]))
nL = dla.shape[1]


def idx(mode, owner, form, val):
    return np.array([i for i, m in enumerate(meta) if m["mode"] == mode and m["owner"] == owner and m["form"] == form and m["valence"] == val])


print("sanity: corr(sum of DLA, actual logit diff) =", round(float(np.corrcoef(dla.sum((1, 2)), ld)[0, 1]), 3))
conds = [("self", "exp"), ("world", "exp"), ("other", "exp"), ("self", "stated")]
D = {}
for mode in ("K", "EU"):
    for o, f in conds:
        p, q = idx(mode, o, f, "pos"), idx(mode, o, f, "neg")
        D[(mode, o, f)] = dla[p].mean(0) - dla[q].mean(0)  # [nL, 2]
        D[(mode, o, f, "ld")] = ld[p].mean() - ld[q].mean()
step = max(1, nL // 12)
for mode in ("K", "EU"):
    print(f"\n=== {mode}: cumulative (attn+mlp) DLA of pos-neg, by layer; final actual logit diff in brackets")
    print("layer " + " ".join(f"{o + '/' + f:>14s}" for o, f in conds))
    for l in list(range(step - 1, nL, step)) + ([nL - 1] if (nL - 1) % step != step - 1 else []):
        print(f"{l:5d} " + " ".join(f"{D[(mode, o, f)][:l + 1].sum():+14.2f}" for o, f in conds))
    print("actual " + " ".join(f"{D[(mode, o, f, 'ld')]:+14.2f}" for o, f in conds))
for mode in ("K", "EU"):
    for o, f in (("world", "exp"), ("self", "exp")):
        d = D[(mode, o, f)]
        flat = [(d[l, c], l, "attn" if c == 0 else "mlp") for l in range(nL) for c in range(2)]
        neg = sorted(flat)[:5]
        posv = sorted(flat, reverse=True)[:5]
        print(f"\n{mode} {o}/{f}: largest positive " + ", ".join(f"L{l}{c}:{v:+.2f}" for v, l, c in posv))
        print(f"{mode} {o}/{f}: largest negative " + ", ".join(f"L{l}{c}:{v:+.2f}" for v, l, c in neg))
