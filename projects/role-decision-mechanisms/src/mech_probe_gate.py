"""Two-pass ownership-probe gating (mechanism-derived method; develop on dev ONLY, then freeze).

Idea: ownership ("is this line in the role's own mind?") is linearly decodable on a line's content tokens in LATE layers,
but decisions read content in EARLY layers (M1, M4, E3c). So: pass 1 = plain forward pass, read each context line's
late-layer representation and score it with a dev-trained ownership direction; pass 2 = block attention from the tail
to the lines scored "not the role's" inside the frozen reading window (same windows as the judge gating).

subcommands
  collect MODEL TAG OUT_PREFIX            dev prompts (s1 EU wording 0, both card orders): per-line mean residual
                                          (content tokens, first 3 tokens skipped) at every 4th layer, unit-normalised;
                                          label 1 = line in the role's card, 0 = line in the other character's card
  train  OUT_PREFIX                       (CPU) difference-of-means direction per layer, AUC on held-out family folds;
                                          picks the layer with the best held-out AUC and the threshold = midpoint of the
                                          projected class means; writes OUT_PREFIX_probe.npz
  gate   MODEL TAG PROBE.npz PROMPTS OUT WINDOW SEG    apply to a prompt set; SEG = sheet (card/json/prose),
                                          dlg (chatlog/chat), story (LifeChoice injection: sentences of the Memory)
"""
import json
import os
import re
import sys

import numpy as np

sub = sys.argv[1]


def label_lines_card(text, role):
    """(line_text, char_start, label) for card-format dev prompts: role card lines -> 1; other card and events -> 0."""
    s0 = text.find("Characters in this story"); s1 = text.rfind("Situation:")
    out, pos, cur = [], s0, None
    for line in text[s0:s1].split("\n"):
        if line.startswith("Character: "):
            cur = line[len("Character: "):].strip()
        elif line.startswith("Events elsewhere"):
            cur = "__events__"
        if line.startswith("- "):
            out.append((line[2:], pos + 2, int(cur == role)))
        elif line.startswith("Attitudes: "):
            out.append((line[len("Attitudes: "):], pos + len("Attitudes: "), int(cur == role)))
        pos += len(line) + 1
    return out


def story_lines(r, text):
    """LifeChoice injection prompts: sentences of the Memory section (including the injected sentence)."""
    a = text.find("1.2. Memory\n") + len("1.2. Memory\n"); b = text.find("\n\n2. Scenario:")
    out = []
    for m in re.finditer(r"[^\n.!?]+(?:[.!?]+|$)", text[a:b]):
        seg = m.group(0).strip()
        if len(seg) > 8:
            out.append((seg, a + m.start() + (len(m.group(0)) - len(m.group(0).lstrip())), -1))
    return out


def span_of(offs, cs, n, skip=0):
    sp = [i for i, (s, e) in enumerate(offs) if s < cs + n and e > cs]
    return sp[skip:] if len(sp) > skip + 1 else sp


if sub == "train":
    pref = sys.argv[2]
    X = np.load(f"{pref}_feat.npy"); meta = [json.loads(l) for l in open(f"{pref}_meta.jsonl")]
    y = np.array([m["label"] for m in meta]); fam = np.array([m["family"] for m in meta]); layers = json.load(open(f"{pref}_layers.json"))
    fams = sorted(set(fam)); folds = [set(fams[0::2]), set(fams[1::2])]

    def auc(p, q):
        v = np.concatenate([p, q]); r = v.argsort().argsort() + 1
        return (r[:len(p)].sum() - len(p) * (len(p) + 1) / 2) / (len(p) * len(q))
    best = None
    for li, L in enumerate(layers):
        Xl = X[:, li, :].astype(np.float32); a = []
        for k in range(2):
            tr = np.isin(fam, list(folds[k])); te = ~tr
            w = Xl[tr & (y == 1)].mean(0) - Xl[tr & (y == 0)].mean(0)
            a.append(auc(Xl[te & (y == 1)] @ w, Xl[te & (y == 0)] @ w))
        print(f"layer {L:3d} held-out AUC {np.mean(a):.3f}")
        if best is None or np.mean(a) > best[1]:
            best = (li, np.mean(a))
    li = best[0]; Xl = X[:, li, :].astype(np.float32)
    w = Xl[y == 1].mean(0) - Xl[y == 0].mean(0)
    thr = float(((Xl[y == 1] @ w).mean() + (Xl[y == 0] @ w).mean()) / 2)
    np.savez(f"{pref}_probe.npz", w=w, thr=thr, layer=layers[li])
    print(f"chosen layer {layers[li]} (held-out AUC {best[1]:.3f}), threshold {thr:.4f}")
    sys.exit(0)

import torch  # noqa: E402
from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: E402
from mech_common import layers_of, letter_ids, render  # noqa: E402

model_dir, tag = sys.argv[2:4]
kw = {"fix_mistral_regex": True} if "mistral" in model_dir.lower() else {}
tok = AutoTokenizer.from_pretrained(model_dir, **kw)
model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=torch.bfloat16, device_map="cuda:0", attn_implementation="eager")
model.eval()
layers = layers_of(model); NL = len(layers)

if sub == "collect":
    outp = sys.argv[4]
    rows = []
    # v1 dev data (s1): every family appears with BOTH card orders, so ownership is not confounded with card position
    # (the s2 dev data alternates card order by family, which confounds position with the family folds).
    for path, keep in (("/home/xiang/rp_mech/s1/data/prompts.jsonl", ("self", "other", "none")),):
        for l in open(path):
            r = json.loads(l)
            if r["mode"] == "EU" and r["para"] == 0 and r["owner"] in keep and r.get("iv", "plain") == "plain":
                rows.append(r)
    LAY = list(range(0, NL + 1, 4)) + ([NL] if NL % 4 else [])
    feats, meta = [], []
    with torch.no_grad():
        for n, r in enumerate(rows):
            text = render(tok, r["messages"], tag)
            role = re.search(r"You are (\w+)\.", text).group(1)
            enc = tok(text, return_tensors="pt", add_special_tokens=False, return_offsets_mapping=True)
            offs = enc.pop("offset_mapping")[0].tolist()
            hs = model(**enc.to(model.device), output_hidden_states=True).hidden_states
            for (lt, cs, lab) in label_lines_card(text, role):
                sp = span_of(offs, cs, len(lt), skip=3)
                v = torch.stack([hs[L][0, sp].float().mean(0) for L in LAY])
                v = v / v.norm(dim=-1, keepdim=True)
                feats.append(v.cpu().numpy().astype(np.float16))
                meta.append(dict(id=r["id"], family=r["family"], owner=r["owner"], label=lab, line=lt[:80]))
            if n % 200 == 0:
                print(n, len(rows), flush=True)
    np.save(f"{outp}_feat.npy", np.stack(feats))
    json.dump(LAY, open(f"{outp}_layers.json", "w"))
    with open(f"{outp}_meta.jsonl", "w") as f:
        for m in meta:
            f.write(json.dumps(m) + "\n")
    print("done", len(meta))
    sys.exit(0)

# ---------------- gate ----------------
probe_path, prompts, out, win, seg = sys.argv[4:9]
P = np.load(probe_path); w = torch.tensor(P["w"], dtype=torch.float32); thr = float(P["thr"]); PL = int(P["layer"])
wlo, whi = [int(x) for x in win.split("-")]
ids = letter_ids(tok)
for _x in "CD":
    ids.setdefault(_x, tok.encode(_x, add_special_tokens=False)[0])
if seg == "story":  # letters follow the "**" answer prefix with no leading space
    ids = {x: tok.encode(x, add_special_tokens=False)[0] for x in "ABCD"}
from seglib import dlg_lines, sheet_lines  # noqa: E402  (same segmentation as the frozen judge gating)
state = {"cfg": None}


def pre_hook(l):
    def hook(mod, args, kwargs):
        if state["cfg"] is None or kwargs.get("attention_mask") is None:
            return None
        m = kwargs["attention_mask"].clone(); neg = torch.finfo(m.dtype).min
        ks = state["cfg"]
        if ks and wlo <= l <= whi:
            m[:, :, torch.tensor(state["tail"], device=m.device)[:, None], torch.tensor(ks, device=m.device)[None, :]] = neg
        kwargs["attention_mask"] = m
        return args, kwargs
    return hook


hs_ = [layers[l].register_forward_pre_hook(pre_hook(l), with_kwargs=True) for l in range(NL)]
FORMS = os.environ.get("FORMS", "exp,stated,none").split(",")
rows = [json.loads(l) for l in open(prompts)]
if seg in ("sheet", "dlg"):
    rows = [r for r in rows if r["mode"] == "EU" and r["para"] == 0 and r["form"] in FORMS]
else:  # story: injection prompts, original order, self/other near + none, first N items
    N = int(os.environ.get("N_ITEMS", "100")); its = []
    for r in rows:
        if r["item"] not in its:
            its.append(r["item"])
    keep = set(its[:N])
    rows = [r for r in rows if r["item"] in keep and r["order"] == "orig" and (r["src"] == "none" or (r["src"] in ("self", "other") and r["pos"] == "near"))]
MAXTOK = int(os.environ.get("MAXTOK", "100000"))
PREFILL = open(f"/home/xiang/rp_mech/lifechoice/prefill_{tag}.txt").read() if seg == "story" else ""
with open(out, "w") as fo, torch.no_grad():
    for n, r in enumerate(rows):
        text = render(tok, r["messages"], tag) + PREFILL
        enc = tok(text, return_tensors="pt", add_special_tokens=False, return_offsets_mapping=True)
        if enc["input_ids"].shape[1] > MAXTOK:
            continue
        offs = enc.pop("offset_mapping")[0].tolist(); enc = enc.to(model.device)
        if seg == "sheet":
            lines = sheet_lines(text); t0 = text.rfind("Situation:")
        elif seg == "dlg":
            lines = dlg_lines(r, text); t0 = text.rfind("Situation:")
        else:
            lines = story_lines(r, text); t0 = text.rfind("2. Scenario:")
        state["tail"] = [i for i, (s, e) in enumerate(offs) if s >= t0]
        state["cfg"] = None
        o = model(**enc, output_hidden_states=True)
        H = o.hidden_states[PL][0].float()
        gated, scores = [], []
        for (lt, cs, _) in lines:
            sp = span_of(offs, cs, len(lt), skip=3)
            v = H[sp].mean(0); v = v / v.norm()
            sc = float(v.cpu() @ w) - thr
            scores.append(round(sc, 4))
            if sc < 0:
                gated += span_of(offs, cs, len(lt))
        lg0 = o.logits[0, -1].float()
        state["cfg"] = gated
        lg1 = model(**enc).logits[0, -1].float()
        state["cfg"] = None
        if seg == "story":
            lp0 = torch.log_softmax(lg0[[ids[x] for x in "ABCD"]], 0); lp1 = torch.log_softmax(lg1[[ids[x] for x in "ABCD"]], 0)
            tp = r["perm"].index(r["target"])
            inj = [i for i, (lt, cs, _) in enumerate(lines) if lt.startswith("Years before, in a situation")]
            res = dict(item=r["item"], src=r["src"], base=float(lp0[tp].exp()), gated=float(lp1[tp].exp()), n_lines=len(lines),
                       n_gated=int(sum(s < 0 for s in scores)), inj_score=(scores[inj[0]] if inj else None))
        else:
            pos, negt = (ids["A"], ids["B"]) if r["pos_letter"] == "A" else (ids["B"], ids["A"])
            res = {k: v for k, v in r.items() if k != "messages"}
            res.update(res={"base": float(lg0[pos] - lg0[negt]), "judge_win": float(lg1[pos] - lg1[negt])}, judged=scores,
                       n_lines=len(lines), n_judge_rm=len(gated), owners=["NA"] * len(lines))
        fo.write(json.dumps(res) + "\n")
        if n % 50 == 0:
            print(n, len(rows), flush=True)
print("done")
