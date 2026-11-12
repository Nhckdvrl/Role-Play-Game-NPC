"""Linear read-out of the role's attitude at the final (decision) token.

Direction = difference of class means (pos - neg valence) in a training set, per layer, estimated on
one half of the families and evaluated on the other half (2 folds, averaged). Option orders are mixed,
so a pure "answer letter" code cancels; what is read is an order-independent attitude/option signal.

For each test condition we report, per layer:
  AUC  : separation of pos vs neg valence along the direction
  gap  : mean projection(pos) - mean projection(neg), divided by the same gap on decision/self/stated
         (how much attitude signal reaches the decision token, relative to a stated attitude)
plus the behavioural logit-difference effect of the same condition, also relative to self/stated.

usage: mech_probe.py ACT_DIR
"""
import json
import sys

import numpy as np

act_dir = sys.argv[1]
meta = [json.loads(l) for l in open(f"{act_dir}/meta.jsonl")]
acts = np.load(f"{act_dir}/acts.npy", mmap_mode="r")
N, L1, D = acts.shape
fams = sorted({m["family"] for m in meta})
folds = [set(fams[0::2]), set(fams[1::2])]
DEC = {"P", "EU"}


def sel(pred):
    return np.array([i for i, m in enumerate(meta) if pred(m)])


def cond(mode_set, owner, form):
    return lambda m: m["mode"] in mode_set and m["owner"] == owner and m["form"] == form and m["valence"] in ("pos", "neg")


TRAIN = {
    "dec_stated": cond(DEC, "self", "stated"),
    "dec_exp": cond(DEC, "self", "exp"),
    "K_exp": cond({"K"}, "self", "exp"),
}
TEST = {
    "dec self stated": cond(DEC, "self", "stated"),
    "dec self exp": cond(DEC, "self", "exp"),
    "dec other exp": cond(DEC, "other", "exp"),
    "dec world exp": cond(DEC, "world", "exp"),
    "dec other stated": cond(DEC, "other", "stated"),
    "K self exp": cond({"K"}, "self", "exp"),
    "K world exp": cond({"K"}, "world", "exp"),
}


def auc(pos, neg):
    allv = np.concatenate([pos, neg])
    ranks = allv.argsort().argsort() + 1
    rp = ranks[: len(pos)].sum()
    return (rp - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


lab = np.array([1 if m["valence"] == "pos" else 0 for m in meta])
famidx = np.array([m["family"] for m in meta])
ld = np.array([m["ld"] for m in meta])

# behaviour: logit-difference effect per test condition relative to dec self stated
print("Behaviour (mean logit diff pos-valence minus neg-valence, pos-letter units):")
beh = {}
for name, pred in TEST.items():
    ix = sel(pred)
    beh[name] = ld[ix][lab[ix] == 1].mean() - ld[ix][lab[ix] == 0].mean()
for name in TEST:
    print(f"  {name:18s} {beh[name]:+6.2f}   relative {beh[name] / beh['dec self stated']:+.2f}")

layers = list(range(0, L1, 4)) + ([L1 - 1] if (L1 - 1) % 4 else [])
for tname, tpred in TRAIN.items():
    print(f"\n=== direction trained on {tname} (AUC / relative gap) ===")
    print("layer  " + "  ".join(f"{n:>18s}" for n in TEST))
    tix = sel(tpred)
    test_ix = {n: sel(p) for n, p in TEST.items()}
    for l in layers:
        X = np.asarray(acts[:, l, :], dtype=np.float32)
        res = {n: [] for n in TEST}
        gaps = {n: [] for n in TEST}
        for k in range(2):
            tr = tix[np.isin(famidx[tix], list(folds[k]))]
            w = X[tr][lab[tr] == 1].mean(0) - X[tr][lab[tr] == 0].mean(0)
            w /= np.linalg.norm(w) + 1e-8
            for n, ix in test_ix.items():
                te = ix[np.isin(famidx[ix], list(folds[1 - k]))]
                s = X[te] @ w
                p, q = s[lab[te] == 1], s[lab[te] == 0]
                res[n].append(auc(p, q))
                gaps[n].append(p.mean() - q.mean())
        ref = np.mean(gaps["dec self stated"])
        cells = [f"{np.mean(res[n]):.2f} / {np.mean(gaps[n]) / ref:+.2f}" for n in TEST]
        print(f"{l:5d}  " + "  ".join(f"{c:>18s}" for c in cells))
