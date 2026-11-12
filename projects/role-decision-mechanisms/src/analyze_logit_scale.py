"""Scale check: role effects in LOGIT units (log p_pos/p_neg), T set. Per family, cost arrangement and mode,
delta = logit(own pos) - logit(own neg); also the no-info cost effect in logits and the interaction
(does the role effect shrink when cost opposes it?).
usage: analyze_logit_scale.py RUN.jsonl [...]"""
import json, math, sys, os
from collections import defaultdict
P = os.environ.get("PROMPTS", "/home/xiang/rp_mech/test/data/prompts.jsonl")
meta = {}
for l in open(P):
    r = json.loads(l); r.pop("messages"); meta[r["id"]] = r
for run in sys.argv[1:]:
    acc = defaultdict(list)
    for l in open(run):
        o = json.loads(l); m = meta[o["id"]]
        lp_pos, lp_neg = (o["lpA"], o["lpB"]) if m["pos_letter"] == "A" else (o["lpB"], o["lpA"])
        acc[(m["mode"], m["conv"], m["family"], m["valence"], m["owner"], m["form"])].append(max(min(lp_pos - lp_neg, 15), -15))
    c = {k: sum(v) / len(v) for k, v in acc.items()}
    fams = sorted({k[2] for k in c})
    def d(modes, convs, o, f):
        v = [c[(md, cv, fa, "pos", o, f)] - c[(md, cv, fa, "neg", o, f)] for md in modes for cv in convs for fa in fams if (md, cv, fa, "pos", o, f) in c]
        return sum(v) / len(v)
    cost = sum(c[(md, "neg_costly", fa, "none", "none", "none")] - c[(md, "pos_costly", fa, "none", "none", "none")] for md in ("P", "EU") for fa in fams) / (2 * len(fams))
    print(f"\n## {run.split('/')[-1]}   cost effect (no info, logits): {cost:+.2f}")
    cols = [("self", "stated"), ("self", "exp"), ("told", "exp"), ("other", "exp"), ("world", "exp")]
    print(f"{'':22s} " + " ".join(f"{o + '/' + f:>12s}" for o, f in cols) + "   other/use  world/use")
    for name, modes, convs in (("K", ["K"], ["na"]), ("dec both costs", ["P", "EU"], ["pos_costly", "neg_costly"]),
                               ("dec cost vs pos", ["P", "EU"], ["pos_costly"]), ("dec cost vs neg", ["P", "EU"], ["neg_costly"])):
        v = [d(modes, convs, o, f) for o, f in cols]
        print(f"{name:22s} " + " ".join(f"{x:+12.2f}" for x in v) + f"   {v[3] / v[1]:9.2f} {v[4] / v[1]:9.2f}")
