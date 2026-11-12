"""Identity slice, attention knockout: how much do K and the decision draw on the OCCUPATION vs the role's own
EXPERIENCE, and in which layers?

Rows: card format, wording 0, valence pos/neg, forms self/occ, self/exp, self/occ_vs_exp; modes EU and K.
Variants (block attention from every tail token -- from "Situation:" (EU) or "Question:" (K) onward -- to a span):
  base | occ@all | exp@all | occ@Qi | exp@Qi   (Qi = the i-th quarter of the layers)
occupation span = the value of the role's "Occupation:" line; experience span = the role's experience sentence.
Output: per row, the logit difference LD = logit(pos option letter) - logit(neg option letter) for each variant.

usage: mech_identity_knock.py MODEL_DIR TAG OUT.jsonl [SPLIT=all|dev|test]
"""
import json
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from families_identity import IFAMILIES
from mech_common import layers_of, letter_ids, render

model_dir, tag, out = sys.argv[1:4]
SPLIT = sys.argv[4] if len(sys.argv) > 4 else "all"
import os
ROUTES = os.environ.get("ROUTES") == "1"
kw = {"fix_mistral_regex": True} if "mistral" in model_dir.lower() else {}
tok = AutoTokenizer.from_pretrained(model_dir, **kw)
model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=torch.bfloat16, device_map="cuda:0", attn_implementation="eager")
if __import__("os").environ.get("LORA"):
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, __import__("os").environ["LORA"]).merge_and_unload()
model.eval()
ids = letter_ids(tok)
layers = layers_of(model)
NL = len(layers)
Q = [(i * NL // 4, (i + 1) * NL // 4 - 1) for i in range(4)]
FAM = {f["id"]: f for f in IFAMILIES}
FLIP = {"pos": "neg", "neg": "pos"}
rows = [r for r in map(json.loads, open("/home/xiang/rp_mech/identity/data/prompts.jsonl"))
        if r["fmt"] == "card" and r["para"] == 0 and r["valence"] in ("pos", "neg") and r["owner"] == "self"
        and r["form"] in ("occ", "exp", "occ_vs_exp") and r["mode"] in ("EU", "K") and (SPLIT == "all" or r["split"] == SPLIT)]


def spans(r, text, offs):
    fam = FAM[r["family"]]
    role = fam["role"]
    out = {}
    if r["form"] in ("occ", "occ_vs_exp"):
        head = f"Character: {role}\nOccupation: "
        a = text.find(head) + len(head)
        occ = fam[f"occ_{r['valence']}"]
        assert text[a:a + len(occ)] == occ, (text[a:a + 40], occ)
        out["occ"] = [i for i, (s, e) in enumerate(offs) if s < a + len(occ) and e > a]
    if r["form"] in ("exp", "occ_vs_exp"):
        ev = FLIP[r["valence"]] if r["form"] == "occ_vs_exp" else r["valence"]
        st = fam[f"exp_{ev}"].format(who=role)
        a = text.find(st)
        assert a >= 0
        out["exp"] = [i for i, (s, e) in enumerate(offs) if s < a + len(st) and e > a]
    return out


state = {"cfg": None}


def pre_hook(l):
    def hook(mod, args, kwargs):
        if state["cfg"] is None or kwargs.get("attention_mask") is None:
            return None
        m = kwargs["attention_mask"].clone()
        neg = torch.finfo(m.dtype).min
        for b, cfg in enumerate(state["cfg"]):
            ks, lo, hi = cfg[:3]
            qs = cfg[3] if len(cfg) > 3 else state["tail"]
            if ks and qs and lo <= l <= hi:
                m[b, :, torch.tensor(qs, device=m.device)[:, None], torch.tensor(ks, device=m.device)[None, :]] = neg
        kwargs["attention_mask"] = m
        return args, kwargs
    return hook


hs = [layers[l].register_forward_pre_hook(pre_hook(l), with_kwargs=True) for l in range(NL)]
with open(out, "w") as fo:
    for n, r in enumerate(rows):
        text = render(tok, r["messages"], tag)
        enc = tok(text, return_tensors="pt", add_special_tokens=False, return_offsets_mapping=True)
        offs = enc.pop("offset_mapping")[0].tolist()
        sp = spans(r, text, offs)
        t0 = text.rfind("Situation:") if r["mode"] == "EU" else text.rfind("Question:")
        state["tail"] = [i for i, (s, e) in enumerate(offs) if s >= t0]
        cfgs, names = [([], 0, -1)], ["base"]
        tail0 = state["tail"][0]
        for k, ks in sp.items():
            cfgs.append((ks, 0, NL - 1)); names.append(f"{k}@all")
            for qi, (lo, hi) in enumerate(Q):
                cfgs.append((ks, lo, hi)); names.append(f"{k}@Q{qi + 1}")
            if ROUTES:
                card = list(range(ks[-1] + 1, tail0))  # every context token after the span, before the tail
                cfgs.append((ks, 0, NL - 1, card)); names.append(f"{k}@card_all")
                cfgs.append((ks, 0, NL - 1, card + state["tail"])); names.append(f"{k}@everything_all")
                for qi, (lo, hi) in enumerate(Q[:2]):
                    cfgs.append((ks, lo, hi, card)); names.append(f"{k}@card_Q{qi + 1}")
                if k == "occ":  # only the role's later NAME mentions in the card
                    role = FAM[r["family"]]["role"]
                    c0, c1 = offs[card[0]][0], offs[tail0][0]
                    occ_chars, j = [], text.find(role, c0)
                    while 0 <= j < c1:
                        occ_chars.append((j, j + len(role))); j = text.find(role, j + 1)
                    nm = [i for i in card if any(offs[i][0] < b and offs[i][1] > a for a, b in occ_chars)]
                    cfgs.append((ks, 0, NL - 1, nm)); names.append("occ@names_all")
                    cfgs.append((ks, 0, NL - 1, [i for i in card if i not in set(nm)])); names.append("occ@cardnonames_all")
        state["cfg"] = cfgs
        with torch.no_grad():
            batch = {k: t.to(model.device).expand(len(cfgs), -1).contiguous() for k, t in enc.items()}
            lg = model(**batch).logits[:, -1].float()
        state["cfg"] = None
        pos, negt = (ids["A"], ids["B"]) if r["pos_letter"] == "A" else (ids["B"], ids["A"])
        res = {nm: float(lg[j, pos] - lg[j, negt]) for j, nm in enumerate(names)}
        m = {k: v for k, v in r.items() if k != "messages"}
        m.update(res=res, quarters=Q)
        if ROUTES and "occ" in sp:
            m["n_name_tok"] = len(nm)
        fo.write(json.dumps(m) + "\n")
        if n % 100 == 0:
            print(n, len(rows), res.get("base"), flush=True)
print("done")
