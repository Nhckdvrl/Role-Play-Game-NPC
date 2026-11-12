"""Accuracy on MMLU (1000) and ARC-Challenge (500), base vs role-decision SFT. usage: analyze_capab.py"""
import json, os
meta = {json.loads(l)["id"]: json.loads(l) for l in open("/home/xiang/rp_mech/capab/prompts.jsonl")}
for tag in ("qwen3_8b", "llama31_8b", "gemma3_12b", "mistral24b"):
    row = []
    for v in ("base", "sft"):
        p = f"/home/xiang/rp_mech/capab/runs/{v}_{tag}.jsonl"
        if not os.path.exists(p):
            row.append(f"{v}: n/a"); continue
        acc = {"mmlu": [], "arc": []}
        for l in open(p):
            o = json.loads(l); m = meta[o["id"]]
            pred = max("ABCD", key=lambda x: o[f"lp{x}"])
            acc[m["src"]].append(pred == m["answer"])
        row.append(f"{v}: MMLU {sum(acc['mmlu']) / len(acc['mmlu']):.3f} ARC {sum(acc['arc']) / len(acc['arc']):.3f}")
    print(f"{tag:12s} " + " | ".join(row))
