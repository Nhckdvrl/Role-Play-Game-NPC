"""E0-G: is "the other person's claim about me is false" linearly readable from the residual stream at the
reply start, WITHOUT any verification cue — and does that readability survive depth?

Features: residual stream (HF hidden_states[layer+1], i.e. output of 0-based block `layer`) at two positions:
  P_user  last token of the probe user message content (before <|im_end|>)
  P_gen   last token of the generation prompt (where the reply's first token is predicted)
Label: 1 = false-premise line, 0 = true-premise line (same conversation, same history).
Train: E1 training contexts (works disjoint from eval), all depths. Test: eval conversations at depths 2/10/20
built from E0-C histories. Control "line_only": the probe line alone as a single user turn (no setup, no
history) — separability there means surface wording, not knowledge of the setup.
"""
import json, argparse, re, os, random
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="/tmp/xiang_rp/models/Qwen3-8B")
ap.add_argument("--train", default="/home/xiang/rp_persona/runs/e1/e1_data_v1.jsonl")
ap.add_argument("--eval_src", default="/home/xiang/rp_persona/runs/e0c/e0c_q8her.jsonl")
ap.add_argument("--eval_data", default="/home/xiang/rp_persona/data/her_mt_eval_v1.jsonl")
ap.add_argument("--eval_probes", default="/home/xiang/rp_persona/data/e0c_probes_v2_validated.jsonl")
ap.add_argument("--layers", default="6,12,18,24,30,35")
ap.add_argument("--max_tokens", type=int, default=12000)
ap.add_argument("--out", default="/home/xiang/rp_persona/runs/e0g/feats_q8.npz")
args = ap.parse_args()

SYS_RE = re.compile(r"<system_thinking>.*?</system_thinking>\s*", re.S)
LAYERS = [int(x) for x in args.layers.split(",")]
tok = AutoTokenizer.from_pretrained(args.model)
model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.bfloat16, device_map="cuda").eval()
END = tok.convert_tokens_to_ids("<|im_end|>")


def trim(msgs):
    while True:
        p = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        ids = tok(p, add_special_tokens=False).input_ids
        if len(ids) <= args.max_tokens or len(msgs) <= 4:
            return ids
        msgs = [msgs[0]] + msgs[3:]


@torch.no_grad()
def feats(msgs):
    ids = trim(msgs)
    ends = [i for i, t in enumerate(ids) if t == END]
    p_user = ends[-1] - 1  # last content token of the final user message
    out = model(torch.tensor([ids], device="cuda"), output_hidden_states=True, use_cache=False)
    hs = out.hidden_states
    return np.stack([np.stack([hs[l + 1][0, p_user].float().cpu().numpy(), hs[l + 1][0, -1].float().cpu().numpy()])
                     for l in LAYERS]), len(ids)  # [L, 2, d]


X, meta = [], []
# ---- train contexts (E1 data): same history, false vs true probe line
for r in map(json.loads, open(args.train)):
    f, n = feats(r["messages"])
    X.append(f); meta.append({"split": "train", "id": r["id"], "depth": r["depth"], "label": int(r["probe"] == "false_premise"), "ctx": "full", "len": n})
    f, n = feats([r["messages"][-1]])
    X.append(f); meta.append({"split": "train", "id": r["id"], "depth": r["depth"], "label": int(r["probe"] == "false_premise"), "ctx": "line_only", "len": n})
print("train feats", len(X), flush=True)

# ---- eval contexts from E0-C histories
convs = {json.loads(l)["id"]: json.loads(l) for l in open(args.eval_data)}
probes = {json.loads(l)["id"]: json.loads(l) for l in open(args.eval_probes)}
nat = {}
for r in map(json.loads, open(args.eval_src)):
    if r["kind"] == "natural":
        nat.setdefault(r["id"], {})[r["turn"]] = r
for cid in sorted(nat):
    for d in (2, 10, 20):
        base = [convs[cid]["messages"][0]]
        for t in range(d):
            base += [{"role": "user", "content": nat[cid][t]["user_text"]},
                     {"role": "assistant", "content": SYS_RE.sub("", nat[cid][t]["raw"]).strip()}]
        for pt in ("false_premise", "true_premise"):
            line = {"role": "user", "content": probes[cid][pt]}
            lab = int(pt == "false_premise")
            valid = probes[cid]["false_valid" if lab else "true_valid"]
            f, n = feats(base + [line])
            X.append(f); meta.append({"split": "eval", "id": cid, "depth": d, "label": lab, "ctx": "full", "len": n, "valid": valid})
            if d == 2:
                f, n = feats([line])
                X.append(f); meta.append({"split": "eval", "id": cid, "depth": 0, "label": lab, "ctx": "line_only", "len": n, "valid": valid})
os.makedirs(os.path.dirname(args.out), exist_ok=True)
np.savez_compressed(args.out, X=np.stack(X).astype(np.float16), meta=json.dumps(meta), layers=np.array(LAYERS))
print("saved", args.out, len(X))
