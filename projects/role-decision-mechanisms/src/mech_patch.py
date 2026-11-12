"""Interchange patching on the decision tail.

The tail = the scene, question and options (everything after the character sheet), identical text
in base and source. At layer l we overwrite the base run's residual stream at either the last token
("last") or every tail token ("tail") with the source run's values, and read the A/B logit diff.

Pair types (EU mode, wording 0, both option orders, both cost arrangements):
  form  : base = self/exp (valence v),  source = self/stated (same v)   -> does the stated form's tail state carry more?
  own   : base = self/exp pos,          source = self/exp neg           -> where the role's own experience enters the tail
  world : base = world/exp pos,         source = world/exp neg          -> where the inaccessible world evidence enters

usage: mech_patch.py MODEL_DIR TAG PROMPTS.jsonl OUT.jsonl [layer_step=2]
"""
import json
import sys

import torch

from mech_common import layers_of, letter_ids, load, render

model_dir, tag, prompts, out = sys.argv[1:5]
step = int(sys.argv[5]) if len(sys.argv) > 5 else 2
tok, model = load(model_dir)
ids = letter_ids(tok)
layers = layers_of(model)
nL = len(layers)
patch_layers = sorted(set(list(range(0, nL, step)) + [nL - 1]))
rows = {}
for l in open(prompts):
    r = json.loads(l)
    if r["mode"] == "EU" and r["para"] == 0:
        rows[r["id"]] = r


def rid(fam, v, o, f, conv, order):
    return f"{fam}|{v}|{o}|{f}|{conv}|EU|0|{order}"


pairs = []
fams = sorted({r["family"] for r in rows.values()})
for fam in fams:
    for conv in ("pos_costly", "neg_costly"):
        for order in (0, 1):
            for v in ("pos", "neg"):
                pairs.append(("form", v, rid(fam, v, "self", "exp", conv, order), rid(fam, v, "self", "stated", conv, order)))
            pairs.append(("own", "pos", rid(fam, "pos", "self", "exp", conv, order), rid(fam, "neg", "self", "exp", conv, order)))
            pairs.append(("world", "pos", rid(fam, "pos", "world", "exp", conv, order), rid(fam, "neg", "world", "exp", conv, order)))


def encode(r):
    text = render(tok, r["messages"], tag)
    start = text.rfind("Situation:")
    enc = tok(text, return_tensors="pt", add_special_tokens=False, return_offsets_mapping=True)
    offs = enc.pop("offset_mapping")[0]
    tail = [i for i, (a, b) in enumerate(offs.tolist()) if a >= start]
    return enc.to(model.device), tail


state = {}


def make_hook(l):
    def hook(mod, inp, out):
        h = out[0] if isinstance(out, tuple) else out
        for k, (layer, span) in enumerate(state["cfg"]):
            if layer == l:
                pos = state["tail"] if span == "tail" else state["tail"][-1:]
                h[k, pos, :] = state["src"][l][0, pos, :]
        return out
    return hook


cache = {}


def cap_hook(l):
    def hook(mod, inp, out):
        h = out[0] if isinstance(out, tuple) else out
        cache[l] = h.detach().clone()
        return out
    return hook


def ld_of(logits, r):
    pos, neg = (ids["A"], ids["B"]) if r["pos_letter"] == "A" else (ids["B"], ids["A"])
    return (logits[:, -1, pos] - logits[:, -1, neg]).float().tolist()


cfgs = [(l, s) for s in ("last", "tail") for l in patch_layers]
with open(out, "w") as fo, torch.no_grad():
    for n, (ptype, v, bid, sid) in enumerate(pairs):
        b, s = rows[bid], rows[sid]
        eb, tb = encode(b)
        es, ts = encode(s)
        assert len(tb) == len(ts), (bid, len(tb), len(ts))
        # source pass: capture every patch layer
        hs = [layers[l].register_forward_hook(cap_hook(l)) for l in patch_layers]
        src_ld = ld_of(model(**es).logits, s)[0]
        for h in hs:
            h.remove()
        # map source tail positions onto base tail positions (same length, aligned at the end)
        state["src"] = {l: cache[l][:, ts, :] for l in patch_layers}
        state["tail"] = tb
        # rewrite src tensors so that index tb[i] <- ts[i]: build a full-length view for indexing convenience
        full = {}
        for l in patch_layers:
            t = torch.zeros((1, eb["input_ids"].shape[1], cache[l].shape[-1]), dtype=cache[l].dtype, device=model.device)
            t[0, tb, :] = state["src"][l][0]
            full[l] = t
        state["src"] = full
        base_ld = ld_of(model(**eb).logits, b)[0]
        hs = [layers[l].register_forward_hook(make_hook(l)) for l in patch_layers]
        res = {}
        for i in range(0, len(cfgs), 21):
            chunk = cfgs[i:i + 21]
            state["cfg"] = chunk
            batch = {k: t.expand(len(chunk), -1).contiguous() for k, t in eb.items()}
            for (l, sp), x in zip(chunk, ld_of(model(**batch).logits, b)):
                res[f"{sp}{l}"] = x
        for h in hs:
            h.remove()
        fo.write(json.dumps(dict(ptype=ptype, valence=v, base=bid, source=sid, base_ld=base_ld, src_ld=src_ld,
                                 n_tail=len(tb), patched=res)) + "\n")
        if n % 40 == 0:
            print(n, len(pairs), ptype, base_ld, src_ld, flush=True)
print("done")
