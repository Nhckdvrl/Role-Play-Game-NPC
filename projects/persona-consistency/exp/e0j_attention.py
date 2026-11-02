"""E0-J: does attention from the reply start to the character setup fade with depth, and does training restore it?

For each eval context (base E0-C history at depth D + false-premise line), run the prompt minus its last token with
a KV cache, then the last token alone with eager attention and output_attentions=True. Report, per layer, the
attention mass (mean over heads) that the generation-start query puts on: the setup span (system message), the
probe line, and the dialogue history. Optionally with a LoRA adapter.
"""
import json, argparse, re, os
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="/tmp/xiang_rp/models/Qwen3-8B")
ap.add_argument("--adapter", default=None)
ap.add_argument("--eval_src", default="/home/xiang/rp_persona/runs/e0c/e0c_q8her.jsonl")
ap.add_argument("--eval_data", default="/home/xiang/rp_persona/data/her_mt_eval_v1.jsonl")
ap.add_argument("--probes", default="/home/xiang/rp_persona/data/e0c_probes_v2_validated.jsonl")
ap.add_argument("--out", required=True)
args = ap.parse_args()

SYS_RE = re.compile(r"<system_thinking>.*?</system_thinking>\s*", re.S)
tok = AutoTokenizer.from_pretrained(args.model)
model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.bfloat16, device_map="cuda", attn_implementation="eager").eval()
if args.adapter:
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, args.adapter).eval()
START = tok.convert_tokens_to_ids("<|im_start|>")

convs = {json.loads(l)["id"]: json.loads(l) for l in open(args.eval_data)}
probes = {json.loads(l)["id"]: json.loads(l) for l in open(args.probes)}
nat = {}
for r in map(json.loads, open(args.eval_src)):
    if r["kind"] == "natural":
        nat.setdefault(r["id"], {})[r["turn"]] = r

rows = []
for cid in sorted(nat):
    if not probes[cid]["false_valid"]:
        continue
    for d in (2, 10, 20):
        msgs = [convs[cid]["messages"][0]]
        for t in range(d):
            msgs += [{"role": "user", "content": nat[cid][t]["user_text"]},
                     {"role": "assistant", "content": SYS_RE.sub("", nat[cid][t]["raw"]).strip()}]
        msgs.append({"role": "user", "content": probes[cid]["false_premise"]})
        p = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False) + "<system_thinking>"
        ids = tok(p, add_special_tokens=False).input_ids
        starts = [i for i, t in enumerate(ids) if t == START]  # message boundaries
        sys_end, probe_start = starts[1], starts[-2]          # system = [0, starts[1]); probe user msg = [starts[-2], starts[-1])
        x = torch.tensor([ids], device="cuda")
        with torch.no_grad():
            out = model(x[:, :-1], use_cache=True)
            att = model(x[:, -1:], past_key_values=out.past_key_values, output_attentions=True, use_cache=True).attentions
        per_layer = []
        for a in att:  # [1, heads, 1, n]
            w = a[0, :, 0].float().mean(0).cpu().numpy()
            per_layer.append([float(w[:sys_end].sum()), float(w[probe_start:starts[-1]].sum()), float(w[sys_end:probe_start].sum())])
        rows.append({"id": cid, "depth": d, "n_tokens": len(ids), "sys_tokens": sys_end, "mass": per_layer})
        del out, att
        torch.cuda.empty_cache()
os.makedirs(os.path.dirname(args.out), exist_ok=True)
json.dump(rows, open(args.out, "w"))
m = lambda d, k, L: np.mean([r["mass"][L][k] for r in rows if r["depth"] == d])
n = len(rows[0]["mass"])
for L in range(0, n, 4):
    print(f"layer {L:2d} setup-mass d2 {m(2,0,L):.3f} d10 {m(10,0,L):.3f} d20 {m(20,0,L):.3f} | probe-line d2 {m(2,1,L):.3f} d20 {m(20,1,L):.3f} | history d20 {m(20,2,L):.3f}")
