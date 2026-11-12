"""Item-level consistency between K and the decision of the same model on the same context.
Item = (family, fmt, valence, owner, form). K score = mean P(Yes); decision score = mean P(pos option) over modes P/EU,
costs, wordings, orders. Report Pearson r across items (contexts that carry role information, i.e. valence != none),
base vs SFT, on the T set and the identity slice.
usage: analyze_k_dec_consistency.py"""
import json, math
from collections import defaultdict
SETS = {"T": ("/home/xiang/rp_mech/test/data/prompts.jsonl", "/home/xiang/rp_mech/test/runs/{t}.jsonl", "/home/xiang/rp_mech/sft/T_sft_{t}.jsonl"),
        "identity": ("/home/xiang/rp_mech/identity/data/prompts.jsonl", "/home/xiang/rp_mech/identity/runs/{t}.jsonl", "/home/xiang/rp_mech/identity/runs/sft_{t}.jsonl")}
def pearson(a, b):
    n = len(a); ma, mb = sum(a) / n, sum(b) / n
    sa = math.sqrt(sum((x - ma) ** 2 for x in a)); sb = math.sqrt(sum((y - mb) ** 2 for y in b))
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb)
for name, (P, base, sft) in SETS.items():
    meta = {}
    for l in open(P):
        r = json.loads(l); r.pop("messages"); meta[r["id"]] = r
    for t in ("qwen3_8b", "llama31_8b", "gemma3_12b", "mistral24b"):
        out = []
        for lab, path in (("base", base.format(t=t)), ("sft", sft.format(t=t))):
            K, D = defaultdict(list), defaultdict(list)
            for l in open(path):
                o = json.loads(l); m = meta.get(o["id"])
                if m is None or m["valence"] == "none": continue
                pa, pb = math.exp(o["lpA"]), math.exp(o["lpB"])
                if pa + pb == 0: continue
                p = (pa if m["pos_letter"] == "A" else pb) / (pa + pb)
                item = (m["family"], m["fmt"], m["valence"], m["owner"], m["form"])
                (K if m["mode"] == "K" else D)[item].append(p)
            items = [i for i in K if i in D]
            k = [sum(K[i]) / len(K[i]) for i in items]; d = [sum(D[i]) / len(D[i]) for i in items]
            out.append(f"{lab} r={pearson(k, d):.2f} (n={len(items)})")
        print(f"{name:8s} {t:12s} " + "  ".join(out))
