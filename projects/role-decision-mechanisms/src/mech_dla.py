"""Direct logit attribution at the final position, per layer and component (attention / MLP).

For each prompt we capture each decoder layer's attention and MLP contributions to the residual stream at
the last position, project them through the final norm (linearised with the final residual's scale) onto
the unembedding difference (pos-pole letter - neg-pole letter), and save the per-layer contributions.
Conditions: K and EU prompts (wording 0) for self/exp, world/exp, other/exp, self/stated (pos and neg).
The analysis compares pos - neg contributions per layer: where does world evidence get written, and is it
cancelled later in K but not in decisions?

usage: mech_dla.py MODEL_DIR TAG PROMPTS.jsonl OUT.npz
"""
import json
import sys

import numpy as np
import torch

from mech_common import layers_of, letter_ids, load, render

model_dir, tag, prompts, out = sys.argv[1:5]
tok, model = load(model_dir)
ids = letter_ids(tok)
layers = layers_of(model)
nL = len(layers)
rows = [r for r in map(json.loads, open(prompts)) if r["mode"] in ("K", "EU") and r["para"] == 0 and r["valence"] in ("pos", "neg")
        and (r["owner"], r["form"]) in (("self", "exp"), ("world", "exp"), ("other", "exp"), ("self", "stated"))]
is_gemma = "gemma" in tag
cap = {}


def mk(name):
    def hook(mod, inp, outp):
        h = outp[0] if isinstance(outp, tuple) else outp
        cap[name] = h[0, -1, :].float()
        return outp
    return hook


hs = []
for i, L in enumerate(layers):
    if is_gemma:
        hs.append(L.post_attention_layernorm.register_forward_hook(mk(f"a{i}")))
        hs.append(L.post_feedforward_layernorm.register_forward_hook(mk(f"m{i}")))
    else:
        hs.append(L.self_attn.register_forward_hook(mk(f"a{i}")))
        hs.append(L.mlp.register_forward_hook(mk(f"m{i}")))
final_norm = model.model.language_model.norm if hasattr(model.model, "language_model") else model.model.norm
W_U = model.get_output_embeddings().weight
res = np.zeros((len(rows), nL, 2), dtype=np.float32)
ld = np.zeros(len(rows), dtype=np.float32)
meta = []
with torch.no_grad():
    for n, r in enumerate(rows):
        enc = tok(render(tok, r["messages"], tag), return_tensors="pt", add_special_tokens=False).to(model.device)
        o = model(**enc, output_hidden_states=True)
        final = o.hidden_states[-1][0, -1, :].float()
        # hidden_states[-1] is already normed in some implementations; use the pre-norm residual from the last layer output
        pre = o.hidden_states[-1][0, -1, :].float() if not hasattr(final_norm, "weight") else None
        pos, neg = (ids["A"], ids["B"]) if r["pos_letter"] == "A" else (ids["B"], ids["A"])
        u = (W_U[pos] - W_U[neg]).float()
        w = final_norm.weight.float()
        scale = (1.0 + w) if is_gemma else w
        # linearise the final RMSNorm with the scale of the summed residual = sum of components + embedding
        comps = [cap[f"a{i}"] for i in range(nL)] + [cap[f"m{i}"] for i in range(nL)]
        resid = o.hidden_states[0][0, -1, :].float() + sum(comps)
        rms = resid.pow(2).mean().sqrt() + 1e-6
        for i in range(nL):
            res[n, i, 0] = float((cap[f"a{i}"] / rms * scale) @ u)
            res[n, i, 1] = float((cap[f"m{i}"] / rms * scale) @ u)
        lg = o.logits[0, -1].float()
        ld[n] = float(lg[pos] - lg[neg])
        meta.append({k: v for k, v in r.items() if k != "messages"})
        if n % 200 == 0:
            print(n, len(rows), ld[n], res[n].sum(), flush=True)
np.savez(out, dla=res, ld=ld, meta=json.dumps(meta))
print("done")
