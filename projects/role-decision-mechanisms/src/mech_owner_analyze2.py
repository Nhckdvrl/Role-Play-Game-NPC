"""Ownership vs position on v1 data (both card orders per family): train 'self vs other' on held-out-family folds with
both orders mixed; also report a 'role card first vs second' position probe for comparison.
usage: mech_owner_analyze2.py OUT_PREFIX"""
import json, sys
import numpy as np
pref = sys.argv[1]
meta = [json.loads(l) for l in open(f"{pref}_meta.jsonl")]
fams = sorted({m["family"] for m in meta}); folds = [set(fams[0::2]), set(fams[1::2])]
kind = np.array([m["kind"] for m in meta]); famv = np.array([m["family"] for m in meta])
first = np.array([(m["blocks"] == "role") == (m["kind"] == "self") for m in meta])  # sentence sits in the FIRST card
def auc(p, q):
    v = np.concatenate([p, q]); r = v.argsort().argsort() + 1
    return (r[:len(p)].sum() - len(p) * (len(p) + 1) / 2) / (len(p) * len(q))
for rep in ("last", "mean"):
    X = np.load(f"{pref}_{rep}.npy", mmap_mode="r")
    print(f"\n=== {rep}: AUC on held-out families (both card orders mixed in train and test)")
    print("layer   owner(self>other)   position(first>second)   owner within first-card only   owner within second-card only")
    for l in range(0, X.shape[1], 4):
        Xl = np.asarray(X[:, l, :], dtype=np.float32); a1, a2, a3, a4 = [], [], [], []
        for k in range(2):
            tr = np.isin(famv, list(folds[k])); te = ~tr
            w = Xl[tr & (kind == "self")].mean(0) - Xl[tr & (kind == "other")].mean(0)
            a1.append(auc(Xl[te & (kind == "self")] @ w, Xl[te & (kind == "other")] @ w))
            u = Xl[tr & first].mean(0) - Xl[tr & ~first].mean(0)
            a2.append(auc(Xl[te & first] @ u, Xl[te & ~first] @ u))
            a3.append(auc(Xl[te & first & (kind == "self")] @ w, Xl[te & first & (kind == "other")] @ w))
            a4.append(auc(Xl[te & ~first & (kind == "self")] @ w, Xl[te & ~first & (kind == "other")] @ w))
        print(f"{l:5d}   {np.mean(a1):17.2f}   {np.mean(a2):22.2f}   {np.mean(a3):28.2f}   {np.mean(a4):29.2f}")
