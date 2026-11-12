"""Is the Knowing answer computed latently when the K question appears inside a decision prompt?

Collect residuals (all layers, unit-normalised) at the last token of the K question text ("...Oswin?") in
  (a) K prompts (v2, mode K): the question the model is about to answer
  (b) S7 q_role decision prompts (mode EU): the same question inserted before the decision, with no answer
Then (analysis) a valence direction trained on (a) self/stated is applied to (a) and (b) for self/exp,
other/exp, world/exp: is the role's attitude (and only the role's) already encoded at the question end?

usage: mech_qend.py MODEL_DIR TAG V2_PROMPTS S7_PROMPTS OUT_PREFIX
"""
import json
import sys

import numpy as np
import torch

from families import FAMILIES
from mech_common import load, render

model_dir, tag, v2p, s7p, outp = sys.argv[1:6]
tok, model = load(model_dir)
FAM = {f["id"]: f for f in FAMILIES}
rows = []
for l in open(v2p):
    r = json.loads(l)
    if r["mode"] == "K":
        r["src"] = "K"
        rows.append(r)
for l in open(s7p):
    r = json.loads(l)
    if r["mode"] == "EU" and r["iv"] == "q_role":
        r["src"] = "dec_qrole"
        rows.append(r)
meta, acts = [], []
with torch.no_grad():
    for n, r in enumerate(rows):
        fam = FAM[r["family"]]
        kq = fam["kq"].format(role=fam["role"])
        text = render(tok, r["messages"], tag)
        a = text.rfind(kq) + len(kq) - 1
        enc = tok(text, return_tensors="pt", add_special_tokens=False, return_offsets_mapping=True)
        offs = enc.pop("offset_mapping")[0].tolist()
        pos = max(i for i, (s, e) in enumerate(offs) if s <= a)
        o = model(**enc.to(model.device), output_hidden_states=True)
        h = torch.stack([x[0, pos, :] for x in o.hidden_states]).float()
        acts.append((h / h.norm(dim=-1, keepdim=True).clamp_min(1e-6)).cpu().numpy().astype(np.float16))
        meta.append({k: v for k, v in r.items() if k != "messages"})
        if n % 500 == 0:
            print(n, len(rows), flush=True)
np.save(f"{outp}_acts.npy", np.stack(acts))
with open(f"{outp}_meta.jsonl", "w") as f:
    for m in meta:
        f.write(json.dumps(m) + "\n")
print("done")
