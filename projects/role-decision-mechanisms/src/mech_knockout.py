"""Attention knockout: does the decision read the source sentence's conclusion (its last token) or its content?

For self/stated, self/exp and world/exp prompts (EU, wording 0), block attention from every TAIL position
(scene, question, options, instruction) to a set of SOURCE positions, in a window of layers:
  all      : every token of the source span (stated attitude line / experience sentence / world event)
  last     : only the source span's last token (where the inferred attitude is decodable, M1d)
  nonlast  : every source token except the last
Implemented by adding -inf to the eager attention mask passed to each decoder layer in the window.
Reads decision sens = LD(pos) - LD(neg).

usage: mech_knockout.py MODEL_DIR TAG PROMPTS.jsonl OUT.jsonl WINDOWS (e.g. "0-11,12-17,18-23,24-29,0-47")
"""
import json
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from build_s2 import world_text
from families import FAMILIES
from mech_common import layers_of, letter_ids, render

model_dir, tag, prompts, out, wins = sys.argv[1:6]
MODE = sys.argv[6] if len(sys.argv) > 6 else "EU"  # EU (decision) or K (knowing)
wins = [tuple(int(x) for x in w.split("-")) for w in wins.split(",")]
kw = {"fix_mistral_regex": True} if "mistral" in model_dir.lower() else {}
tok = AutoTokenizer.from_pretrained(model_dir, **kw)
model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=torch.bfloat16, device_map="cuda:0", attn_implementation="eager")
import os
if os.environ.get("LORA"):
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, os.environ["LORA"]).merge_and_unload()
model.eval()
ids = letter_ids(tok)
layers = layers_of(model)
FAM = {f["id"]: f for f in FAMILIES}
rows = [r for r in map(json.loads, open(prompts)) if r["mode"] == MODE and r["para"] == 0 and r["valence"] in ("pos", "neg")
        and (r["owner"] == "self" or r["owner"] == "world")]


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
    t0 = text.rfind("Situation:") if MODE != "K" else text.rfind("Question:")
    tail = [i for i, (s, e) in enumerate(offs) if s >= t0]
    return enc.to(model.device), src, tail


state = {"cfg": None}


def pre_hook(l):
    def hook(mod, args, kwargs):
        if state["cfg"] is None:
            return None
        m = kwargs.get("attention_mask")
        if m is None:
            return None
        m = m.clone()
        neg = torch.finfo(m.dtype).min
        for b, (win, kind) in enumerate(state["cfg"]):
            if win is None or not (win[0] <= l <= win[1]):
                continue
            ks = state["src"] if kind == "all" else (state["src"][-1:] if kind == "last" else state["src"][:-1])
            q = torch.tensor(state["tail"], device=m.device)[:, None]
            k = torch.tensor(ks, device=m.device)[None, :]
            m[b, :, q, k] = neg
        kwargs["attention_mask"] = m
        return args, kwargs
    return hook


hs = [layers[l].register_forward_pre_hook(pre_hook(l), with_kwargs=True) for l in range(len(layers))]
cfgs = [(None, None)] + [(w, k) for w in wins for k in ("all", "last", "nonlast")]
with open(out, "w") as fo, torch.no_grad():
    for n, r in enumerate(rows):
        e, src, tail = encode(r)
        state["src"], state["tail"] = src, tail
        pos, neg = (ids["A"], ids["B"]) if r["pos_letter"] == "A" else (ids["B"], ids["A"])
        res = {}
        for i in range(0, len(cfgs), 8):
            chunk = cfgs[i:i + 8]
            state["cfg"] = chunk
            batch = {k: t.expand(len(chunk), -1).contiguous() for k, t in e.items()}
            lg = model(**batch).logits[:, -1].float()
            for (w, kind), j in zip(chunk, range(len(chunk))):
                res["base" if w is None else f"{w[0]}-{w[1]}_{kind}"] = float(lg[j, pos] - lg[j, neg])
        state["cfg"] = None
        m = {kk: vv for kk, vv in r.items() if kk != "messages"}
        m["res"] = res
        fo.write(json.dumps(m) + "\n")
        if n % 100 == 0:
            print(n, len(rows), res["base"], flush=True)
print("done")
