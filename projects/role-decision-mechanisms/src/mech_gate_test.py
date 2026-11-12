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
    """(segment_text, char_start, owner_tag) for every fact segment in the context block, for card / json / prose.
    owner_tag is not used for gating (judge-based only); it is 'NA'."""
    starts = [text.find(k) for k in ("Characters in this story", "Game state:", "Background.") if text.find(k) >= 0]
    s0 = min(starts)
    s1 = text.rfind("Situation:")
    block = text[s0:s1]
    out = []
    if block.startswith("Characters in this story"):
        pos = s0
        for line in block.split("\n"):
            if line.startswith("- "):
                out.append((line[2:], pos + 2, "NA"))
            elif line.startswith("Attitudes: "):
                out.append((line[len("Attitudes: "):], pos + len("Attitudes: "), "NA"))
            pos += len(line) + 1
    elif block.startswith("Game state:"):
        pos = s0
        for line in block.split("\n"):
            m = re.match(r'^(\s*)"((?:[^"\\]|\\.)*)",?\s*$', line)
            if m:
                seg = m.group(2)
                out.append((seg, pos + len(m.group(1)) + 1, "NA"))
            pos += len(line) + 1
    else:
        for m in re.finditer(r"[^.!?\n]+(?:\"[^\"]*\")?[^.!?\n]*[.!?]", block):
            seg = m.group(0).strip()
            if len(seg) > 8 and not seg.startswith("Background"):
                out.append((seg, s0 + m.start() + (len(m.group(0)) - len(m.group(0).lstrip())), "NA"))
    return out


CTX = __import__("os").environ.get("JUDGE_CTX") == "1"


def dlg_sheet(r):
    """Clean story text for the judge, for dialogue formats (chatlog / chat): narrator content only."""
    if r["fmt"] == "chatlog":
        c = r["messages"][0]["content"]
        return c[c.find("Story so far:"):c.rfind("Situation:")].strip()
    us = [m["content"] for m in r["messages"][:-1] if m["role"] == "user"]
    us[0] = us[0][us[0].find("Story so far:"):]
    return "\n\n".join(us).strip()


def dlg_lines(r, text):
    """Fact lines (non-header story lines) located in the rendered text, in order."""
    out, cur = [], 0
    for line in dlg_sheet(r).split("\n"):
        line = line.strip()
        if len(line) <= 8 or line.startswith("[") or line.startswith("Story so far"):
            continue
        a = text.find(line, cur)
        if a < 0:
            continue
        out.append((line, a, "NA"))
        cur = a + len(line)
    return out


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


@torch.no_grad()
def judge_batch(role, lines, sheet_text, bs=16):
    prompts, idx = [], []
    for j, line in enumerate(lines):
        for yes_first in (True, False):
            a, b = ("Yes", "No") if yes_first else ("No", "Yes")
            q = f"{sheet_text}\n\nConsider this line from the information above: \"{line}\"\n\nIs this line part of what is in {role}'s own mind, that is, {role}'s own memories, {role}'s own attitudes, or things {role} has been told?\nA. {a}\nB. {b}\nAnswer with the letter A or B only."
            prompts.append(render(tok, [{"role": "user", "content": q}], tag))
            idx.append((j, yes_first))
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    out = [[0.0, 0] for _ in lines]
    for i in range(0, len(prompts), bs):
        e = tok(prompts[i:i + bs], return_tensors="pt", padding=True, add_special_tokens=False).to(model.device)
        lg = model(**e).logits[:, -1].float()
        pr = torch.softmax(lg[:, [ids["A"], ids["B"]]], -1)
        for k, (j, yf) in enumerate(idx[i:i + bs]):
            out[j][0] += float(pr[k, 0] if yf else pr[k, 1]); out[j][1] += 1
    return [s / n for s, n in out]


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
        DLG = r["fmt"] in ("chatlog", "chat")
        lines = dlg_lines(r, text) if DLG else sheet_lines(text)
        enc = tok(text, return_tensors="pt", add_special_tokens=False, return_offsets_mapping=True)
        offs = enc.pop("offset_mapping")[0].tolist()
        enc = enc.to(model.device)
        t0 = text.rfind("Situation:")
        tail = [i for i, (s, e) in enumerate(offs) if s >= t0]
        spans, judge_rm, oracle_rm, pj = [], [], [], []
        if DLG:
            _sheet = dlg_sheet(r)
        else:
            _st = [text.find(k) for k in ("Characters in this story", "Game state:", "Background.") if text.find(k) >= 0]
            _sheet = text[min(_st):text.rfind("Situation:")].strip()
        _todo = [lt for (lt, cs, owner) in lines if (role, lt, _sheet) not in judged]
        if _todo:
            for lt, p in zip(_todo, judge_batch(role, _todo, _sheet)):
                judged[(role, lt, _sheet)] = p
        for (lt, cs, owner) in lines:
            span = [i for i, (s, e) in enumerate(offs) if cs <= s < cs + len(lt)]
            sheet_text = _sheet
            key = (role, lt, sheet_text if CTX else "")
            if key not in judged:
                judged[key] = judge(role, lt, sheet_text)
            p = judged[key]
            pj.append(round(p, 3))
            if p < 0.5:
                judge_rm += span
            pass
        if not hs:
            hs = [layers[l].register_forward_pre_hook(pre_hook(l), with_kwargs=True) for l in range(len(layers))]
        cfgs = [([], 0, -1), (judge_rm, wlo, whi)]
        names = ["base", "judge_win"]
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
