"""E0-A analysis: APC components vs holistic judge, stage attribution, director interventions.

Units: generation rows are nested in items (query) nested in characters; CIs are item-level
bootstrap (resample items, keep all their samples).
"""
import json, argparse, collections, random, statistics as S, re

ap = argparse.ArgumentParser()
ap.add_argument("--tag", default="q8")
ap.add_argument("--dir", default="/home/xiang/rp_persona/runs/e0a")
ap.add_argument("--data", default="/home/xiang/rp_persona/data/apc_eval_v1.jsonl")
ap.add_argument("--out", default=None)
args = ap.parse_args()

items = {json.loads(l)["id"]: json.loads(l) for l in open(args.data)}
gen = {(r["id"], r["cond"], r["sample"]): r for r in map(json.loads, open(f"{args.dir}/gen_{args.tag}.jsonl"))}
apc = {(r["id"], r["cond"], r["sample"]): r for r in map(json.loads, open(f"{args.dir}/gen_{args.tag}.apc.jsonl"))}
try:
    jud = {(r["id"], r["cond"], r["sample"]): r for r in map(json.loads, open(f"{args.dir}/gen_{args.tag}.judge.jsonl"))}
except FileNotFoundError:
    jud = {}

T = 0.5


def row_metrics(k):
    st = apc[k]["stmts"]
    act = [s for s in st if s["gold"]]                     # data-defined active set
    pas = [s for s in st if not s["gold"]]
    vis = lambda s: s.get("visible", (0.0, 0.0))
    m = {
        "act_entail": S.mean(vis(s)[1] > T for s in act),
        "act_contra": S.mean(vis(s)[0] > T for s in act),
        "pas_contra_any": float(any(vis(s)[0] > T for s in pas)),
        "pas_contra_n": sum(vis(s)[0] > T for s in pas),
        "pas_entail_n": sum(vis(s)[1] > T for s in pas),   # passive facts volunteered
        "apc_norm": S.mean(s["g"] * vis(s)[1] + (1 - s["g"]) * (1 - vis(s)[0]) for s in st),
        "g_gold_agree": S.mean((s["g"] > T) == s["gold"] for s in st),
        "words": len(gen[k]["visible"].split()),
    }
    j = jud.get(k, {})
    for f in ("persona", "answer", "natural", "ooc"):
        if isinstance(j.get(f), (int, float)):
            m["j_" + f] = float(j[f])
    return m


M = {k: row_metrics(k) for k in apc}
conds = sorted({k[1] for k in M}, key=lambda c: ["direct", "think", "her_self", "her_empty", "her_oracle", "her_distract"].index(c) if c in ["direct", "think", "her_self", "her_empty", "her_oracle", "her_distract"] else 99)
ids = sorted(items)
rng = random.Random(0)


def boot(cond, field, B=1000, subset=None):
    per_item = {}
    for (i, c, s), m in M.items():
        if c == cond and field in m and (subset is None or subset(i)):
            per_item.setdefault(i, []).append(m[field])
    keys = sorted(per_item)
    if not keys:
        return None
    means = [S.mean(v) for v in per_item.values()]
    point = S.mean(means)
    bs = sorted(S.mean(S.mean(per_item[rng.choice(keys)]) for _ in keys) for _ in range(B))
    return point, bs[int(0.025 * B)], bs[int(0.975 * B)]


out = []
P = lambda *a: out.append(" ".join(str(x) for x in a))
fields = ["act_entail", "act_contra", "pas_contra_any", "pas_contra_n", "pas_entail_n", "apc_norm", "words",
          "j_persona", "j_answer", "j_natural", "j_ooc"]
P(f"## E0-A summary ({args.tag}); item-bootstrap 95% CI; n_items={len(ids)}")
P("cond | " + " | ".join(fields))
for c in conds:
    cells = []
    for f in fields:
        b = boot(c, f)
        cells.append("-" if b is None else f"{b[0]:.2f} [{b[1]:.2f},{b[2]:.2f}]")
    P(c + " | " + " | ".join(cells))

for name, sub in (("original chars (Alice/Bob/Eve)", lambda i: items[i]["original_character"]),
                  ("famous chars", lambda i: not items[i]["original_character"])):
    P(f"\n### {name}")
    for c in conds:
        b1, b2, b3 = boot(c, "act_entail", subset=sub), boot(c, "pas_contra_any", subset=sub), boot(c, "j_persona", subset=sub)
        P(c, "act_entail", f"{b1[0]:.2f}", "pas_contra_any", f"{b2[0]:.2f}", "j_persona", "-" if not b3 else f"{b3[0]:.2f}")

# paired (same item) contrasts
P("\n## Paired contrasts (item-level mean difference, bootstrap 95% CI)")


def paired(c1, c2, field, B=2000):
    d = {}
    for i in ids:
        a = [M[(i, c1, s)][field] for s in range(8) if (i, c1, s) in M and field in M[(i, c1, s)]]
        b = [M[(i, c2, s)][field] for s in range(8) if (i, c2, s) in M and field in M[(i, c2, s)]]
        if a and b:
            d[i] = S.mean(a) - S.mean(b)
    if not d:
        return None
    v = list(d.values())
    bs = sorted(S.mean(rng.choice(v) for _ in v) for _ in range(B))
    return S.mean(v), bs[int(0.025 * B)], bs[int(0.975 * B)]


for c1, c2 in [("her_self", "her_empty"), ("her_oracle", "her_empty"), ("her_distract", "her_empty"),
               ("her_oracle", "her_distract"), ("her_oracle", "her_self"), ("think", "direct"), ("her_self", "direct")]:
    for f in ["act_entail", "pas_entail_n", "j_persona", "j_natural", "j_answer"]:
        r = paired(c1, c2, f)
        if r:
            P(f"{c1} - {c2} | {f}: {r[0]:+.3f} [{r[1]:+.3f},{r[2]:+.3f}]")

# relevance judge vs data-defined gold
P("\nrelevance DeBERTa agreement with data gold (g>0.5 == gold):", f"{S.mean(m['g_gold_agree'] for m in M.values()):.3f}")

# stage attribution on gold-relevant statements, HER-format conditions
P("\n## Stage attribution on gold-relevant statements (entailed = P(e)>0.5)")
for c in ["her_self", "her_oracle", "her_distract", "her_empty"]:
    cnt = collections.Counter()
    for k, r in apc.items():
        if k[1] != c:
            continue
        for s in r["stmts"]:
            if not s["gold"]:
                continue
            D = s.get("director", (0, 0))[1] > T
            R = s.get("role_thinking", (0, 0))[1] > T
            L = s.get("visible", (0, 0))[1] > T
            cnt[(D, R, L)] += 1
    tot = sum(cnt.values())
    d_pos = sum(v for (d, r, l), v in cnt.items() if d)
    d_pos_l = sum(v for (d, r, l), v in cnt.items() if d and l)
    d_neg = tot - d_pos
    d_neg_l = sum(v for (d, r, l), v in cnt.items() if not d and l)
    P(f"{c}: N={tot} P(D)={d_pos / tot:.2f} P(L|D)={d_pos_l / max(d_pos, 1):.2f} P(L|~D)={d_neg_l / max(d_neg, 1):.2f} "
      + " ".join(f"DRL={int(d)}{int(r)}{int(l)}:{v}" for (d, r, l), v in sorted(cnt.items(), reverse=True)))

# within-item: does the self-director mentioning a gold fact predict the line doing so?
P("\n## Correlations (row level, Spearman-like via ranks)")


def spearman(x, y):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i]); r = [0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for t in range(i, j + 1):
                r[o[t]] = (i + j) / 2
            i = j + 1
        return r
    rx, ry = rk(x), rk(y)
    mx, my = S.mean(rx), S.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float("nan")


if jud:
    ks = [k for k in M if "j_persona" in M[k]]
    for f in ["act_entail", "pas_contra_n", "pas_entail_n", "apc_norm", "words"]:
        P(f"rho(j_persona, {f}) = {spearman([M[k]['j_persona'] for k in ks], [M[k][f] for k in ks]):.3f}")
    P(f"rho(j_natural, words) = {spearman([M[k]['j_natural'] for k in ks], [M[k]['words'] for k in ks]):.3f}")
    P(f"rho(j_natural, pas_entail_n) = {spearman([M[k]['j_natural'] for k in ks], [M[k]['pas_entail_n'] for k in ks]):.3f}")

text = "\n".join(out)
print(text)
if args.out:
    open(args.out, "w").write(text + "\n")
