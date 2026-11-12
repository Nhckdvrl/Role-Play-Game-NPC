"""Model-guided access gating.

Step 1 (judge): for every line of the character sheet that is a memory or a world event, ask the model
  "Could <role> know about the following? <line>  A. Yes  B. No" (both option orders averaged).
Step 2 (decide): run the decision prompt while blocking attention from the tail (scene/question/options/
  instruction) to the token spans of the lines judged NOT knowable (P(Yes) < 0.5), in a layer window.
Variants: no gating | gate judged lines in window W | gate judged lines in all layers | oracle gating
  (gate exactly the lines that belong to other characters or world events).
Reads decision sens for self/exp (use), other/exp and world/exp (leaks).

usage: mech_gate.py MODEL_DIR TAG PROMPTS.jsonl OUT.jsonl WINDOW(lo-hi)
"""
import json
import re
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from mech_common import layers_of, letter_ids, render

model_dir, tag, prompts, out, win = sys.argv[1:6]
wlo, whi = [int(x) for x in win.split("-")]
kw = {"fix_mistral_regex": True} if "mistral" in model_dir.lower() else {}
tok = AutoTokenizer.from_pretrained(model_dir, **kw)
model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=torch.bfloat16, device_map="cuda:0", attn_implementation="eager")
model.eval()
ids = letter_ids(tok)
layers = layers_of(model)
FORMS = __import__("os").environ.get("FORMS", "exp,none").split(",")
rows = [r for r in map(json.loads, open(prompts)) if r["mode"] == "EU" and r["para"] == 0 and r["valence"] in ("pos", "neg", "none")
        and r["form"] in FORMS and r.get("iv", "plain") == "plain"]


def sheet_lines(text):
    """(line_text, char_start, owner_tag) for memory lines and world-event lines."""
    out, owner = [], None
    pos = 0
    for line in text.split("\n"):
        m = re.match(r"Character: (\w+)", line)
        if m:
            owner = m.group(1)
        if line.startswith("Events elsewhere"):
            owner = "WORLD"
        if line.startswith("- ") and owner is not None:
            out.append((line[2:], pos + 2, owner))
        elif line.startswith("Attitudes: ") and owner is not None:
            out.append((line[len("Attitudes: "):], pos + len("Attitudes: "), owner))
        pos += len(line) + 1
    return out


CTX = __import__("os").environ.get("JUDGE_CTX") == "1"


@torch.no_grad()
def judge(role, line, sheet_text=""):
    ps = []
    for yes_first in (True, False):
        a, b = ("Yes", "No") if yes_first else ("No", "Yes")
        if CTX:
            if __import__("os").environ.get("JUDGE_V") == "3":
                q = f"{sheet_text}\n\nConsider this line from the information above: \"{line}\"\n\nIs this line part of what is in {role}'s own mind, that is, {role}'s own memories, {role}'s own attitudes, or things {role} has been told?\nA. {a}\nB. {b}\nAnswer with the letter A or B only."
            elif __import__("os").environ.get("JUDGE_V") == "2":
                q = f"{sheet_text}\n\nConsider this line from the information above: \"{line}\"\n\nDoes {role} know about what this line describes, either because it happened to {role} or because someone told {role} about it?\nA. {a}\nB. {b}\nAnswer with the letter A or B only."
            else:
                q = f"{sheet_text}\n\nConsider this line from the information above: \"{line}\"\n\nIs this something {role} personally knows, from {role}'s own memories or attitudes?\nA. {a}\nB. {b}\nAnswer with the letter A or B only."
        else:
            q = f"Here is a fact from a story: \"{line}\"\n\nCould {role} personally know this fact, based on what {role} has experienced or been told?\nA. {a}\nB. {b}\nAnswer with the letter A or B only."
        e = tok(render(tok, [{"role": "user", "content": q}], tag), return_tensors="pt", add_special_tokens=False).to(model.device)
        lg = model(**e).logits[0, -1].float()
        pa, pb = torch.softmax(lg[[ids["A"], ids["B"]]], 0).tolist()
        ps.append(pa if yes_first else pb)
    return sum(ps) / 2


state = {"cfg": None}


def pre_hook(l):
    def hook(mod, args, kwargs):
        if state["cfg"] is None or kwargs.get("attention_mask") is None:
            return None
        m = kwargs["attention_mask"].clone()
        neg = torch.finfo(m.dtype).min
        for b, (ks, lo, hi) in enumerate(state["cfg"]):
            if ks and lo <= l <= hi:
                q = torch.tensor(state["tail"], device=m.device)[:, None]
                k = torch.tensor(ks, device=m.device)[None, :]
                m[b, :, q, k] = neg
        kwargs["attention_mask"] = m
        return args, kwargs
    return hook


judged = {}
hs = []
with open(out, "w") as fo:
    for n, r in enumerate(rows):
        text = render(tok, r["messages"], tag)
        role = re.search(r"You are (\w+)\.", text).group(1)
        lines = sheet_lines(text)
        enc = tok(text, return_tensors="pt", add_special_tokens=False, return_offsets_mapping=True)
        offs = enc.pop("offset_mapping")[0].tolist()
        enc = enc.to(model.device)
        t0 = text.rfind("Situation:")
        tail = [i for i, (s, e) in enumerate(offs) if s >= t0]
        spans, judge_rm, oracle_rm, pj = [], [], [], []
        for (lt, cs, owner) in lines:
            span = [i for i, (s, e) in enumerate(offs) if cs <= s < cs + len(lt)]
            sheet_text = text[text.find("Characters in this story"):text.rfind("Situation:")].strip()
            key = (role, lt, sheet_text if CTX else "")
            if key not in judged:
                judged[key] = judge(role, lt, sheet_text)
            p = judged[key]
            pj.append(round(p, 3))
            if p < 0.5:
                judge_rm += span
            if owner != role:
                oracle_rm += span
        if not hs:
            hs = [layers[l].register_forward_pre_hook(pre_hook(l), with_kwargs=True) for l in range(len(layers))]
        cfgs = [([], 0, -1), (judge_rm, wlo, whi), (judge_rm, 0, len(layers) - 1), (oracle_rm, wlo, whi), (oracle_rm, 0, len(layers) - 1)]
        names = ["base", "judge_win", "judge_all", "oracle_win", "oracle_all"]
        state["tail"], state["cfg"] = tail, cfgs
        with torch.no_grad():
            batch = {k: t.expand(len(cfgs), -1).contiguous() for k, t in enc.items()}
            lg = model(**batch).logits[:, -1].float()
        state["cfg"] = None
        pos, negt = (ids["A"], ids["B"]) if r["pos_letter"] == "A" else (ids["B"], ids["A"])
        res = {nm: float(lg[j, pos] - lg[j, negt]) for j, nm in enumerate(names)}
        m = {k: v for k, v in r.items() if k != "messages"}
        m.update(res=res, judged=pj, n_lines=len(lines), n_judge_rm=len(judge_rm), owners=[o for _, _, o in lines])
        fo.write(json.dumps(m) + "\n")
        if n % 50 == 0:
            print(n, len(rows), res, flush=True)
print("done")
