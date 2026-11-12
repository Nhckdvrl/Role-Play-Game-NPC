"""Does the same amount of attitude signal at the decision token produce the same logit shift in both forms?

For layer l: direction w = class-mean difference on decision/self/stated (other fold).
Per held-out family, regress LD on projection separately per condition, in pos-letter units,
with order-specific intercepts removed by centring within (family, order, cost, mode, para) cells.
Reports slope (logit per unit projection) and the gap decomposition:
  behaviour ratio exp/stated  =  projection ratio  x  slope ratio (approximately).

usage: mech_readout.py ACT_DIR LAYER [LAYER ...]
"""
import json, sys
import numpy as np
act_dir = sys.argv[1]
meta = [json.loads(l) for l in open(f"{act_dir}/meta.jsonl")]
acts = np.load(f"{act_dir}/acts.npy", mmap_mode="r")
fams = sorted({m["family"] for m in meta}); folds = [set(fams[0::2]), set(fams[1::2])]
famv = np.array([m["family"] for m in meta]); lab = np.array([1 if m["valence"] == "pos" else 0 for m in meta])
ld = np.array([m["ld"] for m in meta])
def ix(owner, form, modes=("P", "EU")):
    return np.array([i for i, m in enumerate(meta) if m["mode"] in modes and m["owner"] == owner and m["form"] == form and m["valence"] in ("pos", "neg")])
conds = {"self stated": ix("self", "stated"), "self exp": ix("self", "exp"), "other exp": ix("other", "exp"), "world exp": ix("world", "exp"), "other stated": ix("other", "stated")}
for l in map(int, sys.argv[2:]):
    X = np.asarray(acts[:, l, :], dtype=np.float32)
    out = {c: {"dproj": [], "dld": []} for c in conds}
    for k in range(2):
        tr = conds["self stated"][np.isin(famv[conds["self stated"]], list(folds[k]))]
        w = X[tr][lab[tr] == 1].mean(0) - X[tr][lab[tr] == 0].mean(0); w /= np.linalg.norm(w)
        for c, I in conds.items():
            te = I[np.isin(famv[I], list(folds[1 - k]))]
            # paired pos-neg differences within identical cells (family, conv, mode, para, order)
            key = lambda i: (meta[i]["family"], meta[i]["conv"], meta[i]["mode"], meta[i]["para"], meta[i]["pos_letter"])
            pos = {key(i): i for i in te if lab[i] == 1}; neg = {key(i): i for i in te if lab[i] == 0}
            for kk in pos:
                if kk in neg:
                    out[c]["dproj"].append(float((X[pos[kk]] - X[neg[kk]]) @ w)); out[c]["dld"].append(ld[pos[kk]] - ld[neg[kk]])
    ref_p = np.mean(out["self stated"]["dproj"]); ref_l = np.mean(out["self stated"]["dld"])
    print(f"layer {l}:  condition         proj-shift(rel)  logit-shift(rel)  logit per proj (rel)   corr(dproj,dld)")
    for c in conds:
        p, d = np.array(out[c]["dproj"]), np.array(out[c]["dld"])
        print(f"           {c:15s}   {p.mean()/ref_p:+.2f}            {d.mean()/ref_l:+.2f}             {(d.mean()/p.mean())/(ref_l/ref_p):+.2f}               {np.corrcoef(p,d)[0,1]:+.2f}")
