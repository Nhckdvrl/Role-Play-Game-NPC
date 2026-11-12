"""Ownership probe: does the representation of a memory's CONTENT encode whose memory it is?

For decision prompts (EU, wording 0) in which the same experience sentence appears as
  self   : in the role's card            ("Maren once bought ...")
  other  : in the other character's card ("Bram once bought ...")
  world  : as an unknown world event      ("A traveller once bought ...")
  told   : the role's memory that the other character told the role the story (role-held), and the other's original line
we save unit-normalised residuals (all layers) at (a) the sentence's last token and (b) the mean of its content tokens
excluding the first three tokens (which carry the owner's name). Names differ across families, so a probe that
generalises across held-out families cannot simply read a name: it must encode the relation to the role.

usage: mech_owner.py MODEL_DIR TAG OUT_PREFIX
"""
import json
import sys

import numpy as np
import torch

from build_s2 import world_text
from families import FAMILIES
from mech_common import load, render

model_dir, tag, outp = sys.argv[1:4]
tok, model = load(model_dir)
from families_test import TFAMILIES
FAM = {f["id"]: f for f in FAMILIES + TFAMILIES}
items = []
import os
PATHS = os.environ.get("OWNER_PATHS", "/home/xiang/rp_mech/s2/data/prompts.jsonl,/home/xiang/rp_mech/s11/data/prompts.jsonl").split(",")
for path in PATHS:
    for l in open(path):
        r = json.loads(l)
        if r["mode"] != "EU" or r["para"] != 0 or r["valence"] not in ("pos", "neg") or r["form"] != "exp":
            continue
        fam = FAM[r["family"]]
        exp = fam[f"exp_{r['valence']}"]
        if r["owner"] == "self":
            items.append((r, "self", exp.format(who=fam["role"])))
        elif r["owner"] == "other" and "s11" not in path:
            items.append((r, "other", exp.format(who=fam["other"])))
        elif r["owner"] == "world" and "s11" not in path:
            items.append((r, "world", world_text(exp)))
        elif r["owner"] == "told":
            items.append((r, "told_orig", exp.format(who=fam["other"])))
            items.append((r, "told_line", f"told {fam['role']} the following story"))
meta, A_last, A_mean = [], [], []
with torch.no_grad():
    for n, (r, kind, sent) in enumerate(items):
        text = render(tok, r["messages"], tag)
        if kind == "told_orig":
            a = text.rfind(sent)  # the other's own card line appears after the role's quoted copy only if blocks are ordered so; use last occurrence
            first = text.find(sent)
            # the quoted copy inside the role's told line is preceded by a quote mark
            a = first if text[first - 1] != '"' else text.find(sent, first + 1)
        elif kind == "told_line":
            a = text.find(sent)
            sent = text[a:text.find("\n", a)]
        else:
            a = text.find(sent)
        if a < 0:
            continue
        enc = tok(text, return_tensors="pt", add_special_tokens=False, return_offsets_mapping=True)
        offs = enc.pop("offset_mapping")[0].tolist()
        span = [i for i, (s, e) in enumerate(offs) if a <= s < a + len(sent)]
        o = model(**enc.to(model.device), output_hidden_states=True)
        H = torch.stack([h[0] for h in o.hidden_states])  # [L+1, T, d]
        last = H[:, span[-1], :].float()
        mean = H[:, span[3:] if len(span) > 4 else span, :].float().mean(1)
        A_last.append((last / last.norm(dim=-1, keepdim=True)).cpu().numpy().astype(np.float16))
        A_mean.append((mean / mean.norm(dim=-1, keepdim=True)).cpu().numpy().astype(np.float16))
        meta.append(dict(id=r["id"], family=r["family"], kind=kind, valence=r["valence"], blocks=r.get("blocks", "")))
        if n % 200 == 0:
            print(n, len(items), flush=True)
np.save(f"{outp}_last.npy", np.stack(A_last))
np.save(f"{outp}_mean.npy", np.stack(A_mean))
with open(f"{outp}_meta.jsonl", "w") as f:
    for m in meta:
        f.write(json.dumps(m) + "\n")
print("done")
