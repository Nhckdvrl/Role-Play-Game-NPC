"""Back-patching the character sheet: give the decision access to later-layer (ownership-bound) sheet representations.

For each decision prompt (EU, wording 0): run once and capture the residual stream at layer SRC for every token of
the context block (from "Characters in this story" up to "Situation:"); run again and overwrite those positions at
layer TGT < SRC with the captured SRC states, then read the decision logit difference. Applied to ALL sheet tokens,
with no knowledge of which lines belong to whom.
Conditions: none; self stated/exp; other exp; world exp (pos/neg); both costs and orders.

usage: mech_backpatch.py MODEL_DIR TAG PROMPTS.jsonl OUT.jsonl PAIRS (e.g. "24>12,28>12,24>16,20>8")
"""
import json
import sys

import torch

from mech_common import layers_of, letter_ids, load, render

model_dir, tag, prompts, out, pairs = sys.argv[1:6]
pairs = [tuple(int(x) for x in p.split(">")) for p in pairs.split(",")]
tok, model = load(model_dir)
ids = letter_ids(tok)
layers = layers_of(model)
rows = [r for r in map(json.loads, open(prompts)) if r["mode"] == "EU" and r["para"] == 0 and (
    r["valence"] == "none" or (r["owner"], r["form"]) in (("self", "stated"), ("self", "exp"), ("other", "exp"), ("world", "exp")))]
srcs = sorted({s for s, t in pairs})
cache, state = {}, {"cfg": None}


def cap(l):
    def hook(mod, inp, outp):
        cache[l] = (outp[0] if isinstance(outp, tuple) else outp).detach().clone()
        return outp
    return hook


def patch(l):
    def hook(mod, inp, outp):
        if state["cfg"] is None:
            return outp
        h = outp[0] if isinstance(outp, tuple) else outp
        for b, pr in enumerate(state["cfg"]):
            if pr is not None and pr[1] == l:
                h[b, state["pos"], :] = cache[pr[0]][0, state["pos"], :].to(h.dtype)
        return outp
    return hook


tgts = sorted({t for s, t in pairs})
with open(out, "w") as fo, torch.no_grad():
    for n, r in enumerate(rows):
        text = render(tok, r["messages"], tag)
        enc = tok(text, return_tensors="pt", add_special_tokens=False, return_offsets_mapping=True)
        offs = enc.pop("offset_mapping")[0].tolist()
        enc = enc.to(model.device)
        a, b = text.find("Characters in this story"), text.rfind("Situation:")
        state["pos"] = [i for i, (s, e) in enumerate(offs) if a <= s < b]
        hs = [layers[l].register_forward_hook(cap(l)) for l in srcs]
        lg0 = model(**enc).logits[0, -1].float()
        for h in hs:
            h.remove()
        hs = [layers[l].register_forward_hook(patch(l)) for l in tgts]
        cfg = list(pairs)
        state["cfg"] = cfg
        batch = {k: t.expand(len(cfg), -1).contiguous() for k, t in enc.items()}
        lg = model(**batch).logits[:, -1].float()
        state["cfg"] = None
        for h in hs:
            h.remove()
        pos, neg = (ids["A"], ids["B"]) if r["pos_letter"] == "A" else (ids["B"], ids["A"])
        res = {"base": float(lg0[pos] - lg0[neg])}
        for j, (s, t) in enumerate(cfg):
            res[f"{s}>{t}"] = float(lg[j, pos] - lg[j, neg])
        m = {k: v for k, v in r.items() if k != "messages"}
        m["res"] = res
        fo.write(json.dumps(m) + "\n")
        if n % 100 == 0:
            print(n, len(rows), res, flush=True)
print("done")
