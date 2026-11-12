"""Where in the tail is the role information, and why does the experience form carry less?

Part 1 (segment patching): for pairs form (base self/exp v -> source self/stated v) and world
  (base world pos -> source world neg), patch ONE tail segment at layer l with the source run's values:
  segments = scene, question, pos_option (the option line of the pos pole), neg_option, final (instruction + template).
Part 2 (attention): mean attention mass (heads averaged) from tail segments to the source span
  (the experience sentence / the stated attitude line / the world event), per layer; also per source token.
Part 3 (source probe): residual at the last token of the source span, per layer, saved for valence probing.

usage: mech_sources.py MODEL_DIR TAG PROMPTS.jsonl OUT_PREFIX LAYERS_PATCH(comma) LAYERS_ATTN(lo,hi)
"""
import json
import sys

import numpy as np
import torch

from build_s2 import world_text
from families import FAMILIES
from mech_common import layers_of, letter_ids, render
from transformers import AutoModelForCausalLM, AutoTokenizer

model_dir, tag, prompts, outp, Lp, La = sys.argv[1:7]
Lp = [int(x) for x in Lp.split(",")]
alo, ahi = [int(x) for x in La.split(",")]
kw = {"fix_mistral_regex": True} if "mistral" in model_dir.lower() else {}
tok = AutoTokenizer.from_pretrained(model_dir, **kw)
model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=torch.bfloat16, device_map="cuda:0", attn_implementation="eager")
model.eval()
ids = letter_ids(tok)
layers = layers_of(model)
FAM = {f["id"]: f for f in FAMILIES}
rows = {}
for l in open(prompts):
    r = json.loads(l)
    if r["mode"] == "EU" and r["para"] == 0 and r["valence"] in ("pos", "neg") and (
            (r["owner"] == "self") or (r["owner"] == "world")):
        rows[r["id"]] = r


def source_text(r):
    fam = FAM[r["family"]]
    if r["owner"] == "world":
        return world_text(fam[f"exp_{r['valence']}"])
    return fam[f"{'stated' if r['form'] == 'stated' else 'exp'}_{r['valence']}"].format(who=fam["role"])


def encode(r):
    text = render(tok, r["messages"], tag)
    enc = tok(text, return_tensors="pt", add_special_tokens=False, return_offsets_mapping=True)
    offs = enc.pop("offset_mapping")[0].tolist()
    pos_first = r["pos_letter"] == "A"
    marks = dict(scene=text.rfind("Situation:"), question=text.rfind("What do you do?"),
                 optA=text.rfind("\nA. ") + 1, optB=text.rfind("\nB. ") + 1, final=text.rfind("Answer with"))
    bounds = [("scene", marks["scene"], marks["question"]), ("question", marks["question"], marks["optA"]),
              ("optA", marks["optA"], marks["optB"]), ("optB", marks["optB"], marks["final"]), ("final", marks["final"], len(text) + 1)]
    seg = {}
    for name, a, b in bounds:
        seg[name] = [i for i, (s, e) in enumerate(offs) if a <= s < b]
    seg["pos_option"] = seg["optA"] if pos_first else seg["optB"]
    seg["neg_option"] = seg["optB"] if pos_first else seg["optA"]
    st = source_text(r)
    a = text.find(st)
    assert a >= 0, (r["id"], st)
    src = [i for i, (s, e) in enumerate(offs) if a <= s < a + len(st)]
    return enc.to(model.device), seg, src


def ld_of(logits, r):
    pos, neg = (ids["A"], ids["B"]) if r["pos_letter"] == "A" else (ids["B"], ids["A"])
    return (logits[:, -1, pos] - logits[:, -1, neg]).float().tolist()


cache = {}


def cap(l):
    def hook(mod, inp, out):
        cache[l] = (out[0] if isinstance(out, tuple) else out).detach().clone()
        return out
    return hook


state = {}


def patch(l):
    def hook(mod, inp, out):
        h = out[0] if isinstance(out, tuple) else out
        for k, (layer, segname) in enumerate(state["cfg"]):
            if layer == l:
                pb, ps = state["bseg"][segname], state["sseg"][segname]
                if len(pb) == len(ps) and pb:
                    h[k, pb, :] = state["src"][l][0, ps, :]
        return out
    return hook


SEGS = ["scene", "question", "pos_option", "neg_option", "final"]

# ---------- Part 1: segment patching ----------
pairs = []
fams = sorted({r["family"] for r in rows.values()})
for fam in fams:
    for conv in ("pos_costly", "neg_costly"):
        for order in (0, 1):
            for v in ("pos", "neg"):
                pairs.append(("form", v, f"{fam}|{v}|self|exp|{conv}|EU|0|{order}", f"{fam}|{v}|self|stated|{conv}|EU|0|{order}"))
            pairs.append(("world", "pos", f"{fam}|pos|world|exp|{conv}|EU|0|{order}", f"{fam}|neg|world|exp|{conv}|EU|0|{order}"))
cfgs = [(l, s) for l in Lp for s in SEGS]
with open(f"{outp}_segpatch.jsonl", "w") as fo, torch.no_grad():
    for n, (pt, v, bid, sid) in enumerate(pairs):
        b, s = rows[bid], rows[sid]
        eb, bseg, _ = encode(b)
        es, sseg, _ = encode(s)
        hs = [layers[l].register_forward_hook(cap(l)) for l in Lp]
        src_ld = ld_of(model(**es).logits, s)[0]
        for h in hs:
            h.remove()
        state.update(src=dict(cache), bseg=bseg, sseg=sseg, cfg=cfgs)
        base_ld = ld_of(model(**eb).logits, b)[0]
        hs = [layers[l].register_forward_hook(patch(l)) for l in Lp]
        batch = {k: t.expand(len(cfgs), -1).contiguous() for k, t in eb.items()}
        res = {f"{sg}{l}": x for (l, sg), x in zip(cfgs, ld_of(model(**batch).logits, b))}
        for h in hs:
            h.remove()
        fo.write(json.dumps(dict(ptype=pt, valence=v, base=bid, source=sid, base_ld=base_ld, src_ld=src_ld, patched=res)) + "\n")
        if n % 50 == 0:
            print("seg", n, len(pairs), flush=True)

# ---------- Parts 2 and 3: attention to the source span, and residuals at its last token ----------
meta, srcacts = [], []
with open(f"{outp}_attn.jsonl", "w") as fo, torch.no_grad():
    for n, (rid, r) in enumerate(sorted(rows.items())):
        enc, seg, src = encode(r)
        o = model(**enc, output_attentions=True, output_hidden_states=True)
        att = {}
        for l in range(alo, ahi + 1):
            A = o.attentions[l][0].float().mean(0)  # [q, k], heads averaged
            for sg in SEGS:
                q = seg[sg]
                att[f"{sg}{l}"] = float(A[q][:, src].sum(-1).mean())
        srcacts.append(torch.stack([h[0, src[-1], :] for h in o.hidden_states]).float().cpu().numpy())
        m = {k: v for k, v in r.items() if k != "messages"}
        m.update(n_src=len(src), attn=att)
        fo.write(json.dumps(m) + "\n")
        if n % 100 == 0:
            print("attn", n, len(rows), flush=True)
X = np.stack(srcacts)
nrm = np.linalg.norm(X, axis=-1, keepdims=True)
np.save(f"{outp}_srcacts.npy", (X / np.clip(nrm, 1e-6, None)).astype(np.float16))
print("done")
