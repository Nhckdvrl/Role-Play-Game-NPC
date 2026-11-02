"""E0-G v2 step 2: residual features for minimal pairs (same history, same line; original vs counterfactual setup).

Variants per context: (orig setup, LINE) y=0 | (cf setup, LINE) y=1 | (orig, NEUTRAL) | (cf, NEUTRAL).
The NEUTRAL variants control for anything the setup edit itself (or its mismatch with the history) makes
decodable without the conflicting line. Train contexts: E1 histories (depths 4/8/12/16); eval: E0-C
histories at depths 2/10/20.
"""
import json, argparse, re, os
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="/tmp/xiang_rp/models/Qwen3-8B")
ap.add_argument("--pairs", default="/home/xiang/rp_persona/data/e0g2_minimal_pairs.jsonl")
ap.add_argument("--train", default="/home/xiang/rp_persona/runs/e1/e1_data_v1.jsonl")
ap.add_argument("--eval_src", default="/home/xiang/rp_persona/runs/e0c/e0c_q8her.jsonl")
ap.add_argument("--layers", default="6,12,18,24,30,35")
ap.add_argument("--max_tokens", type=int, default=12000)
ap.add_argument("--out", default="/home/xiang/rp_persona/runs/e0g/feats2_q8.npz")
ap.add_argument("--adapter", default=None, help="LoRA adapter applied to the model")
args = ap.parse_args()

SYS_RE = re.compile(r"<system_thinking>.*?</system_thinking>\s*", re.S)
NEUTRAL = "{user}: Let us rest here a moment; it has been a long day."
LAYERS = [int(x) for x in args.layers.split(",")]
tok = AutoTokenizer.from_pretrained(args.model)
model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.bfloat16, device_map="cuda").eval()
if args.adapter:
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, args.adapter).eval()
END = tok.convert_tokens_to_ids("<|im_end|>")
pairs = {p["id"]: p for p in map(json.loads, open(args.pairs))}


@torch.no_grad()
def feats(msgs):
    while True:
        ids = tok(tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False),
                  add_special_tokens=False).input_ids
        if len(ids) <= args.max_tokens or len(msgs) <= 4:
            break
        msgs = [msgs[0]] + msgs[3:]
    p_user = [i for i, t in enumerate(ids) if t == END][-1] - 1
    hs = model(torch.tensor([ids], device="cuda"), output_hidden_states=True, use_cache=False).hidden_states
    return np.stack([np.stack([hs[l + 1][0, p_user].float().cpu().numpy(), hs[l + 1][0, -1].float().cpu().numpy()])
                     for l in LAYERS])


X, meta = [], []


def add(split, cid, depth, history):
    p = pairs[cid]
    for setup_key, y in (("system", 0), ("system_cf", 1)):
        for kind, line in (("line", p["line"]), ("neutral", NEUTRAL.format(user=p["user"]))):
            X.append(feats([{"role": "system", "content": p[setup_key]}] + history + [{"role": "user", "content": line}]))
            meta.append({"split": split, "id": cid, "depth": depth, "y": y, "kind": kind})


done = set()
for r in map(json.loads, open(args.train)):
    if r["id"] in pairs and (r["id"], r["depth"]) not in done and r["probe"] == "false_premise":
        done.add((r["id"], r["depth"]))
        add("train", r["id"], r["depth"], r["messages"][1:-1])
print("train contexts", len(done), flush=True)
nat = {}
for r in map(json.loads, open(args.eval_src)):
    if r["kind"] == "natural":
        nat.setdefault(r["id"], {})[r["turn"]] = r
for cid in sorted(nat):
    if cid not in pairs:
        continue
    for d in (2, 10, 20):
        hist = []
        for t in range(d):
            hist += [{"role": "user", "content": nat[cid][t]["user_text"]},
                     {"role": "assistant", "content": SYS_RE.sub("", nat[cid][t]["raw"]).strip()}]
        add("eval", cid, d, hist)
os.makedirs(os.path.dirname(args.out), exist_ok=True)
np.savez_compressed(args.out, X=np.stack(X).astype(np.float16), meta=json.dumps(meta), layers=np.array(LAYERS))
print("saved", args.out, len(X))
