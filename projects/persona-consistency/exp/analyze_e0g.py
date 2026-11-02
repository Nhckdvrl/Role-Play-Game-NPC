"""Fit linear probes (false vs true premise) on E1-train features, test on eval contexts by depth.

Reports AUC per layer x position x context type, with a conversation-level bootstrap CI on eval, and
whether the probe score at d20 relates to in-scene acceptance (E0-E full@d20 accepted_false rate).
"""
import json, argparse, collections, random
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

ap = argparse.ArgumentParser()
ap.add_argument("--feats", default="/home/xiang/rp_persona/runs/e0g/feats_q8.npz")
ap.add_argument("--judge_d20", default="/home/xiang/rp_persona/runs/e0e/e0e_q8her_d20.judge.jsonl")
ap.add_argument("--out", default=None)
args = ap.parse_args()

z = np.load(args.feats, allow_pickle=True)
X, meta, layers = z["X"].astype(np.float32), json.loads(str(z["meta"])), list(z["layers"])
rng = random.Random(0)
out = []
P = lambda *a: out.append(" ".join(str(x) for x in a))
idx = lambda **kw: [i for i, m in enumerate(meta) if all(m.get(k) == v for k, v in kw.items())]

acc = collections.defaultdict(list)
for r in map(json.loads, open(args.judge_d20)):
    if r["policy"] == "full" and r["probe"] == "false_premise" and "accepted_false" in r["j"]:
        acc[r["id"]].append(r["j"]["accepted_false"])
acc = {k: float(np.mean(v)) for k, v in acc.items()}


def boot_auc(y, s, ids, B=1000):
    by = collections.defaultdict(list)
    for yi, si, ii in zip(y, s, ids):
        by[ii].append((yi, si))
    keys = list(by)
    vals = []
    for _ in range(B):
        samp = [p for k in (rng.choice(keys) for _ in keys) for p in by[k]]
        yy, ss = zip(*samp)
        if len(set(yy)) == 2:
            vals.append(roc_auc_score(yy, ss))
    vals.sort()
    return roc_auc_score(y, s), vals[int(.025 * len(vals))], vals[int(.975 * len(vals))]


for ctx in ("full", "line_only"):
    P(f"\n## context={ctx}: eval AUC (false vs true premise) by layer/position; train n={len(idx(split='train', ctx=ctx))}")
    for li, L in enumerate(layers):
        for pi, pos in enumerate(("P_user", "P_gen")):
            tr = idx(split="train", ctx=ctx)
            sc = StandardScaler().fit(X[tr, li, pi])
            clf = LogisticRegression(C=0.01, max_iter=2000).fit(sc.transform(X[tr, li, pi]), [meta[i]["label"] for i in tr])
            cells = []
            for d in ((0,) if ctx == "line_only" else (2, 10, 20)):
                te = [i for i in idx(split="eval", ctx=ctx, depth=d) if meta[i]["valid"]]
                s = clf.decision_function(sc.transform(X[te, li, pi]))
                a, lo, hi = boot_auc([meta[i]["label"] for i in te], s, [meta[i]["id"] for i in te])
                cells.append(f"d{d} {a:.2f} [{lo:.2f},{hi:.2f}]")
                if ctx == "full" and d == 20:
                    fs = {meta[i]["id"]: si for i, si in zip(te, s) if meta[i]["label"] == 1}
                    common = [k for k in fs if k in acc]
                    if len(common) > 5:
                        rho = np.corrcoef(np.argsort(np.argsort([fs[k] for k in common])),
                                          np.argsort(np.argsort([acc[k] for k in common])))[0, 1]
                        cells.append(f"rho(score, accept@d20)={rho:+.2f} (n={len(common)})")
            P(f"layer {L:2d} {pos}: " + " | ".join(cells))
text = "\n".join(out)
print(text)
if args.out:
    open(args.out, "w").write(text + "\n")
