"""E0-I: causal test of activation re-anchoring (HF generate with residual hooks).

1. Anchor directions v_L at layers --layers: mean(cued - uncued) residual at the generation start over E1 training
   contexts (as in E0-H), unit-normalised. Restoring magnitude c_L = measured depth drift of the uncued projection
   (d2 minus d20) from E0-H, times --scale.
2. On eval contexts (base E0-C histories at depth 20 + probe line), generate with the HER prefill under:
     none     no intervention
     anchor   residual += c_L * v_L at every position (prompt and generated) of block L
     random   same norms, random unit directions (one fixed draw per layer)
Writes rows compatible with e0c_judge.py (policy = "steer:<cond>").
"""
import json, argparse, re, os, random
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import sys
sys.path.insert(0, os.path.dirname(__file__))
from rp_common import parse_her

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="/tmp/xiang_rp/models/Qwen3-8B")
ap.add_argument("--train", default="/home/xiang/rp_persona/runs/e1/e1_data_v1.jsonl")
ap.add_argument("--anchor_stats", default="/home/xiang/rp_persona/runs/e0g/anchor_q8.json")
ap.add_argument("--eval_src", default="/home/xiang/rp_persona/runs/e0c/e0c_q8her.jsonl")
ap.add_argument("--eval_data", default="/home/xiang/rp_persona/data/her_mt_eval_v1.jsonl")
ap.add_argument("--probes", default="/home/xiang/rp_persona/data/e0c_probes_v2_validated.jsonl")
ap.add_argument("--probe_types", default="false_premise,meta_ai,none")
ap.add_argument("--layers", default="24,30")
ap.add_argument("--scale", type=float, default=1.0)
ap.add_argument("--conds", default="none,anchor,random")
ap.add_argument("--n", type=int, default=4)
ap.add_argument("--n_train", type=int, default=128)
ap.add_argument("--shard", default="0/1", help="i/k: process every k-th context starting at i")
ap.add_argument("--out", required=True)
args = ap.parse_args()

SYS_RE = re.compile(r"<system_thinking>.*?</system_thinking>\s*", re.S)
FMT_RE = re.compile(r"[#*= ]*Response Format[#*= ]*\n.*", re.S)
NOTE = "[Note — {name}'s character setup, for reference:\n{setup}]\n\n"
LAYERS = [int(x) for x in args.layers.split(",")]
tok = AutoTokenizer.from_pretrained(args.model)
model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.bfloat16, device_map="cuda").eval()
blocks = model.model.layers


def render(msgs):
    while True:
        p = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False) + "<system_thinking>"
        ids = tok(p, add_special_tokens=False).input_ids
        if len(ids) <= 14000 or len(msgs) <= 4:
            return ids
        msgs = [msgs[0]] + msgs[3:]


@torch.no_grad()
def last_state(msgs):
    hs = model(torch.tensor([render(msgs)], device="cuda"), output_hidden_states=True, use_cache=False).hidden_states
    return torch.stack([hs[l + 1][0, -1].float() for l in LAYERS])


# ---- anchor directions (same recipe as E0-H) and restoring magnitudes from E0-H depth drift
diffs = []
for r in map(json.loads, open(args.train)):
    if r["probe"] != "false_premise":
        continue
    setup = FMT_RE.sub("", r["messages"][0]["content"]).strip()
    cued = r["messages"][:-1] + [{"role": "user", "content": NOTE.format(name=r["character"], setup=setup) + r["messages"][-1]["content"]}]
    diffs.append(last_state(cued) - last_state(r["messages"]))
    if len(diffs) >= args.n_train:
        break
V = torch.stack(diffs).mean(0)
V = V / V.norm(dim=1, keepdim=True)
st = json.load(open(args.anchor_stats))
li_map = {l: i for i, l in enumerate(st["layers"])}
rows = [r for r in st["rows"] if r["valid"]]
C = []
for l in LAYERS:
    i = li_map[l]
    d2 = np.mean([r["proj_uncued"][i] for r in rows if r["depth"] == 2])
    d20 = np.mean([r["proj_uncued"][i] for r in rows if r["depth"] == 20])
    C.append(float(d2 - d20) * args.scale)
g = torch.Generator().manual_seed(0)
R = torch.randn(V.shape, generator=g)
R = R / R.norm(dim=1, keepdim=True)
print("layers", LAYERS, "restoring magnitudes", [round(c, 2) for c in C], flush=True)

active = {"vec": None}


def make_hook(k):
    def hook(mod, inp, out):
        if active["vec"] is None:
            return out
        h = out[0] if isinstance(out, tuple) else out
        h = h + active["vec"][k].to(h.dtype)
        return (h,) + tuple(out[1:]) if isinstance(out, tuple) else h
    return hook


for k, l in enumerate(LAYERS):
    blocks[l].register_forward_hook(make_hook(k))

convs = {json.loads(l)["id"]: json.loads(l) for l in open(args.eval_data)}
probes = {json.loads(l)["id"]: json.loads(l) for l in open(args.probes)}
nat, natural_next = {}, {}
for r in map(json.loads, open(args.eval_src)):
    if r["kind"] == "natural":
        nat.setdefault(r["id"], {})[r["turn"]] = r
    elif r["kind"] == "probe" and r["probe"] == "none" and r["depth"] == 20 and r["sample"] == 0:
        natural_next[r["id"]] = r["user_text"]
ctxs = [(cid, p) for cid in sorted(nat) for p in args.probe_types.split(",")
        if not (p == "false_premise" and not probes[cid]["false_valid"])]
si, sk = map(int, args.shard.split("/"))
ctxs = ctxs[si::sk]
os.makedirs(os.path.dirname(args.out), exist_ok=True)
with open(args.out, "w") as f:
    for cid, ptype in ctxs:
        msgs = [convs[cid]["messages"][0]]
        for t in range(20):
            msgs += [{"role": "user", "content": nat[cid][t]["user_text"]},
                     {"role": "assistant", "content": SYS_RE.sub("", nat[cid][t]["raw"]).strip()}]
        line = natural_next[cid] if ptype == "none" else probes[cid][ptype]
        ids = torch.tensor([render(msgs + [{"role": "user", "content": line}])], device="cuda")
        for cond in args.conds.split(","):
            active["vec"] = None if cond == "none" else torch.stack(
                [(V if cond == "anchor" else R)[k].cuda() * C[k] for k in range(len(LAYERS))])
            torch.manual_seed(hash((cid, ptype)) % (2 ** 31))
            with torch.no_grad():
                out = model.generate(ids, attention_mask=torch.ones_like(ids), do_sample=True, temperature=0.7, top_p=0.9,
                                     max_new_tokens=700, num_return_sequences=args.n, pad_token_id=tok.eos_token_id)
            for s in range(args.n):
                text = tok.decode(out[s, ids.shape[1]:], skip_special_tokens=True)
                full = "<system_thinking>" + text
                f.write(json.dumps({"id": cid, "character": convs[cid]["character"], "mode": "her", "policy": f"steer:{cond}",
                                    "kind": "probe", "turn": 20, "depth": 20, "probe": ptype, "sample": s,
                                    "user_text": line, "raw": full, **parse_her(full)}, ensure_ascii=False) + "\n")
            f.flush()
        print("done", cid, ptype, flush=True)
active["vec"] = None
print("ALL DONE", flush=True)
