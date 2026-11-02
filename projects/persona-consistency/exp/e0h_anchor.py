"""E0-H: does an "anchored" representational state fade with depth?

Anchor direction v_L (per layer, at the generation start): difference in means between CUED contexts (character
setup restated before the probe line, as in E0-D/E1 "reanchor") and the same contexts UNCUED, over E1 training
contexts (works disjoint from eval). On eval conversations (E0-C histories, depths 2/10/20) we measure, for the
false-premise line, the projection of the uncued state and the cued state on v_L. The cued-minus-uncued gap at a
depth = how far the model's default state is from the anchored state. Joined with acceptance rates at depth 20.
"""
import json, argparse, re, os, collections
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="/tmp/xiang_rp/models/Qwen3-8B")
ap.add_argument("--train", default="/home/xiang/rp_persona/runs/e1/e1_data_v1.jsonl")
ap.add_argument("--eval_src", default="/home/xiang/rp_persona/runs/e0c/e0c_q8her.jsonl")
ap.add_argument("--eval_data", default="/home/xiang/rp_persona/data/her_mt_eval_v1.jsonl")
ap.add_argument("--probes", default="/home/xiang/rp_persona/data/e0c_probes_v2_validated.jsonl")
ap.add_argument("--layers", default="6,12,18,24,30,35")
ap.add_argument("--n_train", type=int, default=256)
ap.add_argument("--out", default="/home/xiang/rp_persona/runs/e0g/anchor_q8.json")
ap.add_argument("--control", action="store_true", help="cue with an UNRELATED character's setup (length-matched control)")
ap.add_argument("--adapter", default=None, help="LoRA adapter to apply to the model (directions still from --load_dirs if given)")
ap.add_argument("--save_dirs", default=None)
ap.add_argument("--load_dirs", default=None, help="reuse saved anchor directions (e.g. the base model's) instead of re-estimating")
args = ap.parse_args()

SYS_RE = re.compile(r"<system_thinking>.*?</system_thinking>\s*", re.S)
FMT_RE = re.compile(r"[#*= ]*Response Format[#*= ]*\n.*", re.S)
NOTE = "[Note — {name}'s character setup, for reference:\n{setup}]\n\n"
LAYERS = [int(x) for x in args.layers.split(",")]
tok = AutoTokenizer.from_pretrained(args.model)
model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.bfloat16, device_map="cuda").eval()
if args.adapter:
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, args.adapter).eval()


@torch.no_grad()
def state(msgs):
    while True:
        p = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False) + "<system_thinking>"
        ids = tok(p, add_special_tokens=False).input_ids
        if len(ids) <= 14000 or len(msgs) <= 4:
            break
        msgs = [msgs[0]] + msgs[3:]
    hs = model(torch.tensor([ids], device="cuda"), output_hidden_states=True, use_cache=False).hidden_states
    return np.stack([hs[l + 1][0, -1].float().cpu().numpy() for l in LAYERS])


POOL = [FMT_RE.sub("", json.loads(l)["messages"][0]["content"]).strip() for l in open(args.train)][::8]


def cue(msgs, name):
    setup = FMT_RE.sub("", msgs[0]["content"]).strip()
    if args.control:  # an unrelated setup of the closest length, never the character's own
        setup = min((s for s in POOL if s != setup), key=lambda s: abs(len(s) - len(setup)))
    return msgs[:-1] + [{"role": "user", "content": NOTE.format(name=name, setup=setup) + msgs[-1]["content"]}]


if args.load_dirs:
    v = np.load(args.load_dirs)
    print("loaded anchor directions", args.load_dirs, flush=True)
else:
    diffs = []
    for i, r in enumerate(map(json.loads, open(args.train))):
        if r["probe"] != "false_premise":
            continue
        diffs.append(state(cue(r["messages"], r["character"])) - state(r["messages"]))
        if len(diffs) >= args.n_train:
            break
    v = np.mean(diffs, 0)
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    print("anchor directions from", len(diffs), "train contexts", flush=True)
if args.save_dirs:
    np.save(args.save_dirs, v)

convs = {json.loads(l)["id"]: json.loads(l) for l in open(args.eval_data)}
probes = {json.loads(l)["id"]: json.loads(l) for l in open(args.probes)}
nat = {}
for r in map(json.loads, open(args.eval_src)):
    if r["kind"] == "natural":
        nat.setdefault(r["id"], {})[r["turn"]] = r
res = []
for cid in sorted(nat):
    for d in (2, 10, 20):
        msgs = [convs[cid]["messages"][0]]
        for t in range(d):
            msgs += [{"role": "user", "content": nat[cid][t]["user_text"]},
                     {"role": "assistant", "content": SYS_RE.sub("", nat[cid][t]["raw"]).strip()}]
        msgs.append({"role": "user", "content": probes[cid]["false_premise"]})
        su, sc = state(msgs), state(cue(msgs, convs[cid]["character"]))
        res.append({"id": cid, "depth": d, "valid": probes[cid]["false_valid"],
                    "proj_uncued": [float(x) for x in (su * v).sum(1)], "proj_cued": [float(x) for x in (sc * v).sum(1)]})
json.dump({"layers": LAYERS, "rows": res}, open(args.out, "w"))
by = collections.defaultdict(list)
for r in res:
    for li, L in enumerate(LAYERS):
        by[(L, r["depth"])].append(r["proj_cued"][li] - r["proj_uncued"][li])
for L in LAYERS:
    print(f"layer {L:2d} cued-uncued gap on anchor dir: " + " | ".join(
        f"d{d} {np.mean(by[(L, d)]):.2f}±{np.std(by[(L, d)]) / np.sqrt(len(by[(L, d)])):.2f}" for d in (2, 10, 20)))
