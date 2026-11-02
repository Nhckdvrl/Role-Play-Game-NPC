"""Trait-enactment summary for E0-A: per condition, per character, and vs. the absolute judge."""
import json, argparse, collections, random, statistics as S

ap = argparse.ArgumentParser()
ap.add_argument("--tag", default="q8")
ap.add_argument("--dir", default="/home/xiang/rp_persona/runs/e0a")
ap.add_argument("--out", default=None)
args = ap.parse_args()

T = [r for r in map(json.loads, open(f"{args.dir}/gen_{args.tag}.traits.jsonl")) if r["labels"]]
J = {(r["id"], r["cond"], r["sample"]): r for r in map(json.loads, open(f"{args.dir}/gen_{args.tag}.judge.jsonl"))}
rng = random.Random(0)
out = []
P = lambda *a: out.append(" ".join(str(x) for x in a))
M = {}
for r in T:
    L = r["labels"]
    M[(r["id"], r["cond"], r["sample"])] = {"E": L.count("E") / len(L), "V": L.count("V") / len(L),
                                             "anyV": float("V" in L), "n": len(L)}
conds = ["direct", "think", "her_self", "her_empty", "her_oracle", "her_distract"]


def agg(cond, f, sub=lambda i: True, B=1000):
    per = {}
    for (i, c, s), m in M.items():
        if c == cond and sub(i):
            per.setdefault(i, []).append(m[f])
    v = [S.mean(x) for x in per.values()]
    if not v:
        return "-"
    bs = sorted(S.mean(rng.choice(v) for _ in v) for _ in range(B))
    return f"{S.mean(v):.3f} [{bs[25]:.3f},{bs[975]:.3f}]"


P(f"## Trait enactment ({args.tag}); rows={len(M)}; mean traits/row={S.mean(m['n'] for m in M.values()):.1f}")
P("cond | E share | V share | any-V rate")
for c in conds:
    P(c, "|", agg(c, "E"), "|", agg(c, "V"), "|", agg(c, "anyV"))

P("\n## any-V rate by character (pooled over conditions)")
byc = collections.defaultdict(list)
for (i, c, s), m in M.items():
    byc[i.split("-")[0]].append(m["anyV"])
for ch, v in sorted(byc.items(), key=lambda x: -S.mean(x[1])):
    P(f"{ch}: {S.mean(v):.3f} (n={len(v)})")


def paired(c1, c2, f, B=2000):
    d = []
    for i in sorted({k[0] for k in M}):
        a = [M[(i, c1, s)][f] for s in range(4) if (i, c1, s) in M]
        b = [M[(i, c2, s)][f] for s in range(4) if (i, c2, s) in M]
        if a and b:
            d.append(S.mean(a) - S.mean(b))
    bs = sorted(S.mean(rng.choice(d) for _ in d) for _ in range(B))
    return f"{S.mean(d):+.3f} [{bs[int(.025 * B)]:+.3f},{bs[int(.975 * B)]:+.3f}]"


P("\n## Paired contrasts")
for c1, c2 in [("think", "direct"), ("her_self", "direct"), ("her_self", "her_empty"), ("her_oracle", "her_distract")]:
    P(f"{c1}-{c2}: E {paired(c1, c2, 'E')} | anyV {paired(c1, c2, 'anyV')}")

ks = [k for k in M if k in J and isinstance(J[k].get("persona"), int)]
v1 = [J[k]["persona"] for k in ks if M[k]["anyV"]]
v0 = [J[k]["persona"] for k in ks if not M[k]["anyV"]]
P(f"\nabsolute judge persona | any-V rows: {S.mean(v1):.2f} (n={len(v1)}) vs no-V rows: {S.mean(v0):.2f} (n={len(v0)})")
P(f"share of any-V rows that the absolute judge still scored >=9: {sum(x >= 9 for x in v1) / max(1, len(v1)):.2f}")
text = "\n".join(out)
print(text)
if args.out:
    open(args.out, "w").write(text + "\n")
