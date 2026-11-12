"""Thinking ON vs OFF (Qwen3), EU wording 0. sens = P(pos)|pos - P(pos)|neg, from final answers (think) or A/B probs (no think).
usage: think_analyze.py TAG NOTHINK_RUN.jsonl"""
import json, math, sys
from collections import defaultdict
tag, nt = sys.argv[1:3]
meta = {json.loads(l)["id"]: json.loads(l) for l in open("/home/xiang/rp_mech/think/data/prompts.jsonl")}
def agg(pairs):
    c = defaultdict(list)
    for rid, p in pairs:
        m = meta[rid]; c[(m["family"], m["valence"], m["owner"], m["form"])].append(p)
    return {k: sum(v) / len(v) for k, v in c.items()}
th, bad = [], 0
for l in open(f"/home/xiang/rp_mech/think/runs/{tag}.jsonl"):
    o = json.loads(l)
    if o["answer"] is None: bad += 1; continue
    th.append((o["id"], 1.0 if o["answer"] == meta[o["id"]]["pos_letter"] else 0.0))
no = []
for l in open(nt):
    o = json.loads(l)
    if o["id"] in meta:
        pa, pb = math.exp(o["lpA"]), math.exp(o["lpB"]); m = meta[o["id"]]
        no.append((o["id"], (pa if m["pos_letter"] == "A" else pb) / (pa + pb)))
fams = sorted({m["family"] for m in meta.values()})
print(f"{tag}: unparsed think answers {bad}")
for name, c in (("no-think", agg(no)), ("think", agg(th))):
    def s(o, f):
        v = [c[(fa, "pos", o, f)] - c[(fa, "neg", o, f)] for fa in fams if (fa, "pos", o, f) in c and (fa, "neg", o, f) in c]
        return sum(v) / len(v)
    print(f"  {name:9s} self stated {s('self','stated'):+.2f}  self exp {s('self','exp'):+.2f}  other exp {s('other','exp'):+.2f}  world exp {s('world','exp'):+.2f}")
