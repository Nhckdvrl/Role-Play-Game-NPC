"""Is the attitude direction causally used by the decision?

Direction w_l = class-mean difference (pos - neg valence) of final-token residuals on decision/self/stated
prompts at layer l, from ACT_DIR (computed on the *other* half of the families than the ones steered).
We add  s * alpha * g_l * w_l  to the residual stream of the last token at layer l, where g_l is the
mean projection gap between pos and neg stated prompts (so alpha=1 adds one "stated-sized" attitude shift)
and s = +1 for pos-valence prompts and -1 for neg-valence prompts (pushes toward the role's attitude).
A random unit direction of the same norm is the control.

Measured on decision prompts (EU, wording 0, both orders and cost arrangements) for conditions:
  self/exp (weak behaviour), self/stated (strong), none (no attitude; s chosen as +1 to read the raw shift)
Output: sens (LD_pos - LD_neg) per (condition, layer, alpha, direction type).

usage: mech_steer.py MODEL_DIR TAG PROMPTS.jsonl ACT_DIR OUT.jsonl LAYERS(comma) ALPHAS(comma)
"""
import json
import sys

import numpy as np
import torch

from mech_common import layers_of, letter_ids, load, render

model_dir, tag, prompts, act_dir, out, Ls, As = sys.argv[1:8]
Ls = [int(x) for x in Ls.split(",")]
As = [float(x) for x in As.split(",")]
meta = [json.loads(l) for l in open(f"{act_dir}/meta.jsonl")]
acts = np.load(f"{act_dir}/acts.npy", mmap_mode="r")
normed = __import__("os").path.exists(f"{act_dir}/norms.npy") and np.load(f"{act_dir}/norms.npy").mean() > 0
fams = sorted({m["family"] for m in meta})
folds = [set(fams[0::2]), set(fams[1::2])]
lab = np.array([1 if m["valence"] == "pos" else 0 for m in meta])
famv = np.array([m["family"] for m in meta])
tr_all = np.array([i for i, m in enumerate(meta) if m["mode"] in ("P", "EU") and m["owner"] == "self"
                   and m["form"] == "stated" and m["valence"] in ("pos", "neg")])

tok, model = load(model_dir)
ids = letter_ids(tok)
layers = layers_of(model)
rng = np.random.default_rng(0)

# directions per fold and layer (raw scale; if acts were stored unit-normalised, rescale by stored norms)
norms = np.load(f"{act_dir}/norms.npy") if __import__("os").path.exists(f"{act_dir}/norms.npy") else None
dirs = {}
for k in range(2):
    tr = tr_all[np.isin(famv[tr_all], list(folds[k]))]
    for l in Ls:
        X = np.asarray(acts[tr, l + 1, :], dtype=np.float32)  # hidden_states[l+1] = output of decoder layer l
        if norms is not None and np.abs(np.linalg.norm(X, axis=1) - 1).max() < 0.05:
            X = X * norms[tr, l + 1][:, None]
        diff = X[lab[tr] == 1].mean(0) - X[lab[tr] == 0].mean(0)
        g = float(np.linalg.norm(diff))
        w = diff / g
        r = rng.standard_normal(w.shape).astype(np.float32)
        r /= np.linalg.norm(r)
        dirs[(k, l)] = (torch.tensor(w), torch.tensor(r), g)

rows = [json.loads(l) for l in open(prompts)]
rows = [r for r in rows if r["mode"] == "EU" and r["para"] == 0 and r["valence"] in ("pos", "neg", "none")
        and ((r["owner"] == "self") or r["owner"] == "none")]
state = {"vec": None}


def hook_for(l):
    def hook(mod, inp, outp):
        if state["vec"] is not None and state["layer"] == l:
            h = outp[0] if isinstance(outp, tuple) else outp
            h[:, -1, :] += state["vec"].to(h.dtype).to(h.device)
        return outp
    return hook


hs = [layers[l].register_forward_hook(hook_for(l)) for l in Ls]
with open(out, "w") as fo, torch.no_grad():
    for n, r in enumerate(rows):
        k = 1 if r["family"] in folds[0] else 0  # direction from the other fold
        enc = tok(render(tok, r["messages"], tag), return_tensors="pt", add_special_tokens=False).to(model.device)
        pos, neg = (ids["A"], ids["B"]) if r["pos_letter"] == "A" else (ids["B"], ids["A"])
        s = -1.0 if r["valence"] == "neg" else 1.0
        res = {}
        state["vec"] = None
        lg = model(**enc).logits[0, -1].float()
        res["base"] = float(lg[pos] - lg[neg])
        for l in Ls:
            w, rv, g = dirs[(k, l)]
            for a in As:
                for name, v in (("dir", w), ("rand", rv)):
                    state["vec"], state["layer"] = s * a * g * v, l
                    lg = model(**enc).logits[0, -1].float()
                    res[f"{name}_L{l}_a{a}"] = float(lg[pos] - lg[neg])
        state["vec"] = None
        m = {kk: vv for kk, vv in r.items() if kk != "messages"}
        m["res"] = res
        fo.write(json.dumps(m) + "\n")
        if n % 50 == 0:
            print(n, len(rows), flush=True)
print("done")
