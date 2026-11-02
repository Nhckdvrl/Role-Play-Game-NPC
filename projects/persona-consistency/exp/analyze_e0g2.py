"""E0-G v2 analysis: is setup/line conflict linearly readable (minimal pairs), and does it survive depth?

For each layer x position: train logistic probe (orig vs cf setup) on train contexts, evaluate AUC on eval
contexts per depth — separately for LINE variants (conflict present in cf) and NEUTRAL variants (no conflicting
line; measures edit/history-mismatch artifacts). The informative quantity is LINE AUC well above NEUTRAL AUC.
"""
import json, argparse, collections, random
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

ap = argparse.ArgumentParser()
ap.add_argument("--feats", default="/home/xiang/rp_persona/runs/e0g/feats2_q8.npz")
ap.add_argument("--out", default=None)
args = ap.parse_args()
z = np.load(args.feats, allow_pickle=True)
X, meta, layers = z["X"].astype(np.float32), json.loads(str(z["meta"])), list(z["layers"])
rng = random.Random(0)
idx = lambda **kw: [i for i, m in enumerate(meta) if all(m.get(k) == v for k, v in kw.items())]
out = []
P = lambda *a: out.append(" ".join(str(x) for x in a))


def boot(y, s, ids, B=1000):
    by = collections.defaultdict(list)
    for a, b, c in zip(y, s, ids):
        by[c].append((a, b))
    keys, vals = list(by), []
    for _ in range(B):
        smp = [p for k in (rng.choice(keys) for _ in keys) for p in by[k]]
        yy, ss = zip(*smp)
        if len(set(yy)) == 2:
            vals.append(roc_auc_score(yy, ss))
    vals.sort()
    return roc_auc_score(y, s), vals[int(.025 * len(vals))], vals[int(.975 * len(vals))]


P(f"train contexts={len(idx(split='train', kind='line')) // 2}, eval contexts={len(idx(split='eval', kind='line')) // 2}")
for kind in ("line", "neutral"):
    P(f"\n## variants={kind}: eval AUC (orig vs counterfactual setup) by depth")
    for li, L in enumerate(layers):
        for pi, pos in enumerate(("P_user", "P_gen")):
            tr = idx(split="train", kind=kind)
            sc = StandardScaler().fit(X[tr, li, pi])
            clf = LogisticRegression(C=0.01, max_iter=3000).fit(sc.transform(X[tr, li, pi]), [meta[i]["y"] for i in tr])
            cells = []
            for d in (2, 10, 20):
                te = idx(split="eval", kind=kind, depth=d)
                a, lo, hi = boot([meta[i]["y"] for i in te], clf.decision_function(sc.transform(X[te, li, pi])), [meta[i]["id"] for i in te])
                cells.append(f"d{d} {a:.2f} [{lo:.2f},{hi:.2f}]")
            P(f"layer {L:2d} {pos}: " + " | ".join(cells))
text = "\n".join(out)
print(text)
if args.out:
    open(args.out, "w").write(text + "\n")
