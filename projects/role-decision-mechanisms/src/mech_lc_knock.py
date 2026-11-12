"""Natural-context mechanism check: does the effect of an injected precedent sentence in a real long story flow through
the same early reading window? Block attention from the tail (from "2. Scenario:" on) to the injected sentence
in all layers / each quarter of layers. Items: first N items of the E3 sample, src self/other, position near,
original option order. Output: P(target) and log-odds of the target vs the mean of the others, per variant.
usage: mech_lc_knock.py MODEL_DIR TAG OUT.jsonl [N=100]"""
import json, math, re, sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from mech_common import layers_of, render

model_dir, tag, out = sys.argv[1:4]
N = int(sys.argv[4]) if len(sys.argv) > 4 else 100
import os
MAXTOK = int(os.environ.get("MAXTOK", "100000"))
kw = {"fix_mistral_regex": True} if "mistral" in model_dir.lower() else {}
tok = AutoTokenizer.from_pretrained(model_dir, **kw)
model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=torch.bfloat16, device_map="cuda:0", attn_implementation="eager")
model.eval()
layers = layers_of(model); NL = len(layers)
Q = [(i * NL // 4, (i + 1) * NL // 4 - 1) for i in range(4)]
PREFILL = open(f"/home/xiang/rp_mech/lifechoice/prefill_{tag}.txt").read()
rows = [json.loads(l) for l in open("/home/xiang/rp_mech/lc_inject/prompts.jsonl")]
items = []
for r in rows:
    if r["item"] not in items:
        items.append(r["item"])
items = set(items[:N])
rows = [r for r in rows if r["item"] in items and r["order"] == "orig" and (r["src"] == "none" or (r["src"] in ("self", "other") and r["pos"] == "near"))]
letter_ids = []
for x in "ABCD":
    ids = tok.encode(x, add_special_tokens=False)
    letter_ids.append(ids[0])
state = {"cfg": None}
def pre_hook(l):
    def hook(mod, args, kwargs):
        if state["cfg"] is None or kwargs.get("attention_mask") is None:
            return None
        m = kwargs["attention_mask"].clone(); neg = torch.finfo(m.dtype).min
        ks, lo, hi = state["cfg"]
        if ks and lo <= l <= hi:
            m[:, :, torch.tensor(state["tail"], device=m.device)[:, None], torch.tensor(ks, device=m.device)[None, :]] = neg
        kwargs["attention_mask"] = m
        return args, kwargs
    return hook
hs = [layers[l].register_forward_pre_hook(pre_hook(l), with_kwargs=True) for l in range(NL)]
with open(out, "w") as fo, torch.no_grad():
    for n, r in enumerate(rows):
        text = render(tok, r["messages"], tag) + PREFILL
        enc = tok(text, return_tensors="pt", add_special_tokens=False, return_offsets_mapping=True)
        if enc["input_ids"].shape[1] > MAXTOK:  # eager attention memory; skipped items are logged
            fo.write(json.dumps(dict(item=r["item"], src=r["src"], skipped=int(enc["input_ids"].shape[1]))) + "\n"); continue
        offs = enc.pop("offset_mapping")[0].tolist(); enc = enc.to(model.device)
        t0 = text.rfind("2. Scenario:")
        state["tail"] = [i for i, (s, e) in enumerate(offs) if s >= t0]
        span = []
        if r["src"] != "none":
            m = re.search(r"(Years before, in a situation much like this one,[^\n]*)", text)
            a, b = m.start(1), m.end(1)
            span = [i for i, (s, e) in enumerate(offs) if s < b and e > a]
        variants = [("base", ([], 0, -1))] + ([("all", (span, 0, NL - 1))] + [(f"Q{i + 1}", (span, lo, hi)) for i, (lo, hi) in enumerate(Q)] if span else [])
        res = {}
        for name, cfg in variants:
            state["cfg"] = cfg
            lg = model(**enc).logits[0, -1].float()
            state["cfg"] = None
            lp = torch.log_softmax(lg[letter_ids], 0).tolist()
            tpos = r["perm"].index(r["target"])
            res[name] = math.exp(lp[tpos])
        fo.write(json.dumps(dict(item=r["item"], src=r["src"], res=res, quarters=Q)) + "\n")
        if n % 20 == 0:
            print(n, len(rows), res, flush=True)
print("done")
