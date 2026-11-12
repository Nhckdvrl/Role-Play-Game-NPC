"""Collect final-token residual streams (all layers) and the A/B logit difference.

usage: mech_collect.py MODEL_DIR TAG PROMPTS.jsonl OUT_DIR [modes=K,P,EU]
Writes OUT_DIR/acts.npy  float16 [N, n_layers+1, d]   (index 0 = embeddings)
       OUT_DIR/meta.jsonl one row per prompt: metadata + ld (logit[pos letter] - logit[neg letter]) + top token
"""
import json
import os
import sys

import numpy as np
import torch

from mech_common import letter_ids, load, render

model_dir, tag, prompts, out = sys.argv[1:5]
modes = set((sys.argv[5] if len(sys.argv) > 5 else "K,P,EU").split(","))
os.makedirs(out, exist_ok=True)
tok, model = load(model_dir)
tok.padding_side = "left"
ids = letter_ids(tok)
rows = [json.loads(l) for l in open(prompts)]
rows = [r for r in rows if r["mode"] in modes]
texts = [render(tok, r["messages"], tag) for r in rows]
n_layers = model.config.get_text_config().num_hidden_layers
d = model.config.get_text_config().hidden_size
acts = np.lib.format.open_memmap(f"{out}/acts.npy", mode="w+", dtype=np.float16, shape=(len(rows), n_layers + 1, d))
NORM = os.environ.get("NORM") == "1"  # store unit vectors (and norms separately) for models whose residuals overflow fp16
norms = np.zeros((len(rows), n_layers + 1), dtype=np.float32)
print("prompts", len(rows), "layers", n_layers, "d", d, "letter ids", ids, flush=True)
bs = 8
with open(f"{out}/meta.jsonl", "w") as fm, torch.no_grad():
    for i in range(0, len(rows), bs):
        enc = tok(texts[i:i + bs], return_tensors="pt", padding=True, add_special_tokens=False).to(model.device)
        o = model(**enc, output_hidden_states=True)
        hs = torch.stack([h[:, -1, :] for h in o.hidden_states], dim=1)  # [b, L+1, d]
        hf = hs.float()
        nr = hf.norm(dim=-1)
        norms[i:i + len(hs)] = nr.cpu().numpy()
        if NORM:
            hf = hf / nr.unsqueeze(-1).clamp_min(1e-6)
        acts[i:i + len(hs)] = hf.cpu().numpy().astype(np.float16)
        lg = o.logits[:, -1, :].float()
        for j, r in enumerate(rows[i:i + bs]):
            pos, neg = (ids["A"], ids["B"]) if r["pos_letter"] == "A" else (ids["B"], ids["A"])
            m = {k: v for k, v in r.items() if k != "messages"}
            m["ld"] = float(lg[j, pos] - lg[j, neg])
            m["top"] = tok.decode([int(lg[j].argmax())])
            fm.write(json.dumps(m) + "\n")
        if i % 400 == 0:
            print(i, flush=True)
acts.flush()
np.save(f"{out}/norms.npy", norms)
print("done", out)
