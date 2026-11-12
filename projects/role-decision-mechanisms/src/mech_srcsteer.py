"""Is the weak decision effect of an experience inherited from a weak attitude signal at the experience itself?

Phase 1: raw residuals at the last token of the source span (stated attitude line / experience sentence /
world event) at the chosen layers, for self/stated, self/exp, world/exp (EU, wording 0).
Direction w_l = class-mean difference (pos - neg) on self/stated sources from the OTHER half of the families;
g_l = that gap (raw units).
Phase 2: add  s * alpha * g_l * w_l  at the source span (last token, or every source token), s = +1 for pos, -1 for neg.
  alpha = +0.5 : roughly lifts an experience (~0.5 of stated at the source) to stated size
  alpha = +1.0 : beyond stated size
  alpha = -0.5 : roughly removes the attitude signal of an experience / world event
Read decision sens = LD(pos) - LD(neg).

usage: mech_srcsteer.py MODEL_DIR TAG PROMPTS.jsonl OUT.jsonl LAYERS(comma) ALPHAS(comma)
"""
import json
import sys

import numpy as np
import torch

from build_s2 import world_text
from families import FAMILIES
from mech_common import layers_of, letter_ids, load, render

model_dir, tag, prompts, out, Ls, As = sys.argv[1:7]
Ls = [int(x) for x in Ls.split(",")]
As = [float(x) for x in As.split(",")]
tok, model = load(model_dir)
ids = letter_ids(tok)
layers = layers_of(model)
FAM = {f["id"]: f for f in FAMILIES}
rows = []
for l in open(prompts):
    r = json.loads(l)
    if r["mode"] == "EU" and r["para"] == 0 and r["valence"] in ("pos", "neg") and (
            (r["owner"] == "self") or (r["owner"] == "world")):
        rows.append(r)


def source_text(r):
    fam = FAM[r["family"]]
    if r["owner"] == "world":
        return world_text(fam[f"exp_{r['valence']}"])
    return fam[f"{'stated' if r['form'] == 'stated' else 'exp'}_{r['valence']}"].format(who=fam["role"])


def encode(r):
    text = render(tok, r["messages"], tag)
    enc = tok(text, return_tensors="pt", add_special_tokens=False, return_offsets_mapping=True)
    offs = enc.pop("offset_mapping")[0].tolist()
    st = source_text(r)
    a = text.find(st)
    src = [i for i, (s, e) in enumerate(offs) if a <= s < a + len(st)]
    return enc.to(model.device), src


cache = {}


def cap(l):
    def hook(mod, inp, outp):
        cache[l] = (outp[0] if isinstance(outp, tuple) else outp).detach()
        return outp
    return hook


enc_cache = {r["id"]: encode(r) for r in rows}
raw = {l: {} for l in Ls}
hs = [layers[l].register_forward_hook(cap(l)) for l in Ls]
with torch.no_grad():
    for r in rows:
        if r["owner"] == "self" and r["form"] == "stated":
            e, src = enc_cache[r["id"]]
            model(**e)
            for l in Ls:
                raw[l][r["id"]] = cache[l][0, src[-1], :].float().cpu()
for h in hs:
    h.remove()
fams = sorted({r["family"] for r in rows})
folds = [set(fams[0::2]), set(fams[1::2])]
dirs = {}
for k in range(2):
    for l in Ls:
        P = [v for i, v in raw[l].items() if i.split("|")[0] in folds[k] and i.split("|")[1] == "pos"]
        N = [v for i, v in raw[l].items() if i.split("|")[0] in folds[k] and i.split("|")[1] == "neg"]
        d = torch.stack(P).mean(0) - torch.stack(N).mean(0)
        g = d.norm()
        dirs[(k, l)] = (d / g, float(g))
print("source gaps (raw):", {l: round(dirs[(0, l)][1], 2) for l in Ls}, flush=True)

state = {"cfg": None}


def steer(l):
    def hook(mod, inp, outp):
        if state["cfg"] is None:
            return outp
        h = outp[0] if isinstance(outp, tuple) else outp
        for b, (layer, span, vec) in enumerate(state["cfg"]):
            if layer == l and vec is not None:
                pos = state["src"] if span == "all" else state["src"][-1:]
                h[b, pos, :] += vec.to(h.dtype).to(h.device)
        return outp
    return hook


def ld_of(logits, r):
    pos, neg = (ids["A"], ids["B"]) if r["pos_letter"] == "A" else (ids["B"], ids["A"])
    return (logits[:, -1, pos] - logits[:, -1, neg]).float().tolist()


hs = [layers[l].register_forward_hook(steer(l)) for l in Ls]
with open(out, "w") as fo, torch.no_grad():
    for n, r in enumerate(rows):
        e, src = enc_cache[r["id"]]
        k = 1 if r["family"] in folds[0] else 0
        s = 1.0 if r["valence"] == "pos" else -1.0
        cfg = [(None, None, None)]
        for l in Ls:
            w, g = dirs[(k, l)]
            for span in ("last", "all"):
                for a in As:
                    cfg.append((l, span, s * a * g * w))
        state["src"] = src
        res = {}
        for i in range(0, len(cfg), 16):
            chunk = cfg[i:i + 16]
            state["cfg"] = chunk
            batch = {kk: t.expand(len(chunk), -1).contiguous() for kk, t in e.items()}
            for (l, span, v), x in zip(chunk, ld_of(model(**batch).logits, r)):
                if l is None:
                    res["base"] = x
                else:
                    a = round(float((v.norm() / dirs[(k, l)][1]).item()) * (1 if (v @ dirs[(k, l)][0]).item() * s > 0 else -1), 2)
                    res[f"L{l}_{span}_a{a}"] = x
        state["cfg"] = None
        m = {kk: vv for kk, vv in r.items() if kk != "messages"}
        m["res"] = res
        fo.write(json.dumps(m) + "\n")
        if n % 100 == 0:
            print(n, len(rows), flush=True)
print("done")
