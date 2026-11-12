"""Summarise mech_sources.py outputs.

usage: mech_sources_analyze.py OUT_PREFIX
"""
import json
import sys
from collections import defaultdict

import numpy as np

pref = sys.argv[1]
# ---- Part 1 ----
rows = [json.loads(l) for l in open(f"{pref}_segpatch.jsonl")]
keys = list(rows[0]["patched"].keys())
units = defaultdict(dict)
for r in rows:
    fam, _, _, _, conv, _, _, order = r["base"].split("|")
    units[(r["ptype"], fam, conv, order)][r["valence"]] = r
segs = sorted({k.rstrip("0123456789") for k in keys}, key=["scene", "question", "pos_option", "neg_option", "final"].index)
Ls = sorted({int(k[len(k.rstrip("0123456789")):]) for k in keys})
num, den = defaultdict(float), 0.0
for (pt, *_), u in units.items():
    if pt == "form" and len(u) == 2:
        se = u["pos"]["base_ld"] - u["neg"]["base_ld"]
        ss = u["pos"]["src_ld"] - u["neg"]["src_ld"]
        den += ss - se
        for k in keys:
            num[k] += (u["pos"]["patched"][k] - u["neg"]["patched"][k]) - se
print("Part 1a. FORM restoration by patching ONE tail segment (exp -> stated)")
print("layer  " + "  ".join(f"{s:>10s}" for s in segs))
for l in Ls:
    print(f"{l:5d}  " + "  ".join(f"{num[f'{s}{l}']/den:+10.2f}" for s in segs))
num, den = defaultdict(float), 0.0
for (pt, *_), u in units.items():
    if pt == "world":
        r = u["pos"]
        den += r["base_ld"] - r["src_ld"]
        for k in keys:
            num[k] += r["base_ld"] - r["patched"][k]
print("Part 1b. WORLD leak transferred by patching ONE tail segment (pos -> neg event)")
print("layer  " + "  ".join(f"{s:>10s}" for s in segs))
for l in Ls:
    print(f"{l:5d}  " + "  ".join(f"{num[f'{s}{l}']/den:+10.2f}" for s in segs))

# ---- Part 2 ----
A = [json.loads(l) for l in open(f"{pref}_attn.jsonl")]
groups = {"self stated": lambda m: m["owner"] == "self" and m["form"] == "stated",
          "self exp": lambda m: m["owner"] == "self" and m["form"] == "exp",
          "world exp": lambda m: m["owner"] == "world"}
ak = list(A[0]["attn"].keys())
aL = sorted({int(k[len(k.rstrip("0123456789")):]) for k in ak})
print("\nPart 2. Attention mass from tail segments to the source span (heads averaged); per-token mass in brackets")
for sg in ("pos_option", "neg_option", "question", "final", "scene"):
    print(f"  segment {sg}:")
    print("    layer  " + "  ".join(f"{g:>20s}" for g in groups))
    for l in aL[::2]:
        cells = []
        for g, pred in groups.items():
            ms = [m for m in A if pred(m)]
            tot = np.mean([m["attn"][f"{sg}{l}"] for m in ms])
            per = np.mean([m["attn"][f"{sg}{l}"] / m["n_src"] for m in ms])
            cells.append(f"{tot:.4f} [{per:.5f}]")
        print(f"    {l:5d}  " + "  ".join(f"{c:>20s}" for c in cells))
print("  mean source length (tokens): " + ", ".join(f"{g} {np.mean([m['n_src'] for m in A if p(m)]):.1f}" for g, p in groups.items()))

# ---- Part 3 ----
X = np.load(f"{pref}_srcacts.npy", mmap_mode="r")
fams = sorted({m["family"] for m in A})
folds = [set(fams[0::2]), set(fams[1::2])]
lab = np.array([1 if m["valence"] == "pos" else 0 for m in A])
famv = np.array([m["family"] for m in A])


def auc(p, q):
    v = np.concatenate([p, q]); r = v.argsort().argsort() + 1
    return (r[:len(p)].sum() - len(p) * (len(p) + 1) / 2) / (len(p) * len(q))


idx = {g: np.array([i for i, m in enumerate(A) if p(m)]) for g, p in groups.items()}
print("\nPart 3. Valence read-out at the LAST TOKEN OF THE SOURCE SPAN (direction from other half of families)")
print("    train -> test:   " + "  ".join(f"{a}->{b}" for a in ("self stated", "self exp") for b in groups))
for l in range(0, X.shape[1], 4):
    Xl = np.asarray(X[:, l, :], dtype=np.float32)
    cells = []
    for a in ("self stated", "self exp"):
        for b in groups:
            vals = []
            for k in range(2):
                tr = idx[a][np.isin(famv[idx[a]], list(folds[k]))]
                te = idx[b][np.isin(famv[idx[b]], list(folds[1 - k]))]
                w = Xl[tr][lab[tr] == 1].mean(0) - Xl[tr][lab[tr] == 0].mean(0)
                s = Xl[te] @ w
                vals.append(auc(s[lab[te] == 1], s[lab[te] == 0]))
            cells.append(f"{np.mean(vals):.2f}")
    print(f"    layer {l:3d}:      " + "  ".join(f"{c:>10s}" for c in cells))
