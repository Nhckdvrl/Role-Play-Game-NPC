"""Analyse mech_qend.py: valence read-out at the end of the K question.

Direction = class-mean difference on K prompts, self/stated, at the K-question end (other half of families).
Report AUC and gap relative to K self/stated for:
  K prompts: self/exp, other/exp, world/exp
  decision prompts with the q_role question inserted: self/stated, self/exp, other/exp, world/exp

usage: mech_qend_analyze.py OUT_PREFIX
"""
import json
import sys

import numpy as np

pref = sys.argv[1]
meta = [json.loads(l) for l in open(f"{pref}_meta.jsonl")]
X = np.load(f"{pref}_acts.npy", mmap_mode="r")
fams = sorted({m["family"] for m in meta})
folds = [set(fams[0::2]), set(fams[1::2])]
lab = np.array([1 if m["valence"] == "pos" else 0 for m in meta])
famv = np.array([m["family"] for m in meta])


def ix(src, owner, form):
    return np.array([i for i, m in enumerate(meta) if m["src"] == src and m["owner"] == owner and m["form"] == form and m["valence"] in ("pos", "neg")])


def auc(p, q):
    v = np.concatenate([p, q]); r = v.argsort().argsort() + 1
    return (r[:len(p)].sum() - len(p) * (len(p) + 1) / 2) / (len(p) * len(q))


train = ix("K", "self", "stated")
tests = {"K self st": train, "K self exp": ix("K", "self", "exp"), "K other exp": ix("K", "other", "exp"), "K world exp": ix("K", "world", "exp"),
         "Dq self st": ix("dec_qrole", "self", "stated"), "Dq self exp": ix("dec_qrole", "self", "exp"),
         "Dq other exp": ix("dec_qrole", "other", "exp"), "Dq world exp": ix("dec_qrole", "world", "exp")}
print("AUC / gap relative to 'K self st'   (K = Knowing prompt; Dq = decision prompt with the K question inserted, no answer)")
print("layer " + " ".join(f"{n:>13s}" for n in tests))
for l in range(4, X.shape[1], 4):
    Xl = np.asarray(X[:, l, :], dtype=np.float32)
    res = {n: [] for n in tests}; gap = {n: [] for n in tests}
    for k in range(2):
        tr = train[np.isin(famv[train], list(folds[k]))]
        w = Xl[tr][lab[tr] == 1].mean(0) - Xl[tr][lab[tr] == 0].mean(0)
        for n, I in tests.items():
            te = I[np.isin(famv[I], list(folds[1 - k]))]
            s = Xl[te] @ w
            res[n].append(auc(s[lab[te] == 1], s[lab[te] == 0])); gap[n].append(s[lab[te] == 1].mean() - s[lab[te] == 0].mean())
    ref = np.mean(gap["K self st"])
    print(f"{l:5d} " + " ".join(f"{np.mean(res[n]):.2f}/{np.mean(gap[n])/ref:+.2f}".rjust(13) for n in tests))
