"""Role-play-trained Llama-3.1-8B variants vs Llama-3.1-8B-Instruct, on dev v2 and the T set.
Reports A/B probability mass (format following), K and decision sens for self/other/world (+ told on T).
usage: rp_compare.py
"""
import json
import math
from collections import defaultdict

RUNS = {
    "llama31_8b_instruct": ("/home/xiang/rp_mech/s2/runs/llama31_8b.jsonl", "/home/xiang/rp_mech/test/runs/llama31_8b.jsonl"),
    "coser8b": ("/home/xiang/rp_mech/rpmodels/runs/v2_coser8b.jsonl", "/home/xiang/rp_mech/rpmodels/runs/T_coser8b.jsonl"),
    "rolemrc_sft": ("/home/xiang/rp_mech/rpmodels/runs/v2_rolemrc_sft.jsonl", "/home/xiang/rp_mech/rpmodels/runs/T_rolemrc_sft.jsonl"),
    "rolemrc_dpo": ("/home/xiang/rp_mech/rpmodels/runs/v2_rolemrc_dpo.jsonl", "/home/xiang/rp_mech/rpmodels/runs/T_rolemrc_dpo.jsonl"),
    "qwen3_8b_sft(ref)": (None, "/home/xiang/rp_mech/sft/T_sft_qwen3_8b.jsonl"),
}
META = {}
for p in ("/home/xiang/rp_mech/s2/data/prompts.jsonl", "/home/xiang/rp_mech/test/data/prompts.jsonl"):
    for l in open(p):
        r = json.loads(l)
        r.pop("messages")
        META[r["id"]] = r


def summarize(path):
    acc, mass = defaultdict(list), []
    for l in open(path):
        o = json.loads(l)
        m = META[o["id"]]
        pa, pb = math.exp(o["lpA"]), math.exp(o["lpB"])
        mass.append(pa + pb)
        if pa + pb == 0:
            continue
        task = "K" if m["mode"] == "K" else "dec"
        acc[(task, m["family"], m["valence"], m["owner"], m["form"])].append((pa if m["pos_letter"] == "A" else pb) / (pa + pb))
    c = {k: sum(v) / len(v) for k, v in acc.items()}
    fams = sorted({k[1] for k in c})

    def s(task, o, f):
        v = [c[(task, fa, "pos", o, f)] - c[(task, fa, "neg", o, f)] for fa in fams if (task, fa, "pos", o, f) in c and (task, fa, "neg", o, f) in c]
        return sum(v) / len(v) if v else float("nan")
    return sum(mass) / len(mass), s


print(f"{'model':20s} {'set':4s} {'A+B mass':>8s} | {'K self exp':>10s} {'K world':>8s} | {'dec stated':>10s} {'dec exp':>8s} {'dec told':>8s} {'dec other':>9s} {'dec world':>9s}")
for name, (v2, T) in RUNS.items():
    for setname, path in (("dev", v2), ("T", T)):
        if not path:
            continue
        try:
            mass, s = summarize(path)
        except FileNotFoundError:
            continue
        print(f"{name:20s} {setname:4s} {mass:8.2f} | {s('K', 'self', 'exp'):+10.2f} {s('K', 'world', 'exp'):+8.2f} | {s('dec', 'self', 'stated'):+10.2f} {s('dec', 'self', 'exp'):+8.2f} {s('dec', 'told', 'exp'):+8.2f} {s('dec', 'other', 'exp'):+9.2f} {s('dec', 'world', 'exp'):+9.2f}")
