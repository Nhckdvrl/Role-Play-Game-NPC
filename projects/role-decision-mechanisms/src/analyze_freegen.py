"""Free-generation validity: classify each sampled reply (two judges, two option orders) into pos / neg / unclear,
then compute sens = P(pos | pos) - P(pos | neg) among clear replies, per owner/form, and judge agreement.
usage: analyze_freegen.py TAG"""
import json, math, random, sys
from collections import defaultdict
tag = sys.argv[1]; D = "/home/xiang/rp_mech/freegen"
gmeta = {json.loads(l)["id"]: json.loads(l) for l in open(f"{D}/gen.jsonl")}
jmeta = {json.loads(l)["id"]: json.loads(l) for l in open(f"{D}/runs/judgeprompts_{tag}.jsonl")}
def labels(judge):
    acc = defaultdict(lambda: [0.0, 0.0, 0.0])
    for l in open(f"{D}/runs/judge{judge}_{tag}.jsonl"):
        o = json.loads(l); m = jmeta[o["id"]]
        ps = [math.exp(o.get(f"lp{x}", -math.inf)) for x in "ABC"]; z = sum(ps) or 1.0; ps = [p / z for p in ps]
        pos, neg = (ps[0], ps[1]) if m["pos_letter"] == "A" else (ps[1], ps[0])
        a = acc[m["gen_id"]]; a[0] += pos; a[1] += neg; a[2] += ps[2]
    return {k: ["pos", "neg", "unclear"][max(range(3), key=lambda i: v[i])] for k, v in acc.items()}
LM, LG = labels("M"), labels("G")
common = [k for k in LM if k in LG]
agree = sum(LM[k] == LG[k] for k in common) / len(common)
print(f"######## {tag}: {len(common)} replies; judge agreement (Mistral vs Gemma) = {agree:.2f}; unclear rate M {sum(LM[k]=='unclear' for k in common)/len(common):.2f} G {sum(LG[k]=='unclear' for k in common)/len(common):.2f}")
cols = [("self", "stated"), ("self", "exp"), ("told", "exp"), ("other", "exp"), ("world", "exp")]
for jn, L in (("judge Mistral", LM), ("judge Gemma", LG), ("agreed only", {k: LM[k] for k in common if LM[k] == LG[k]})):
    c = defaultdict(list)
    for k, lab in L.items():
        if lab == "unclear": continue
        m = gmeta[k.split("#")[0]]
        c[(m["family"], m["valence"], m["owner"], m["form"])].append(1.0 if lab == "pos" else 0.0)
    fams = sorted({k[0] for k in c})
    row = []
    for o, f in cols:
        xs = [sum(c[(fa, "pos", o, f)]) / len(c[(fa, "pos", o, f)]) - sum(c[(fa, "neg", o, f)]) / len(c[(fa, "neg", o, f)])
              for fa in fams if c.get((fa, "pos", o, f)) and c.get((fa, "neg", o, f))]
        rng = random.Random(0); bs = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(2000)) if xs else [0]
        row.append(f"{o}/{f} {sum(xs)/len(xs):+.2f} [{bs[50]:+.2f},{bs[-50]:+.2f}]" if xs else f"{o}/{f} n/a")
    print(f"  {jn:14s} " + "  ".join(row))
