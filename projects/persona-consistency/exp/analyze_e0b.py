"""E0-B analysis: does near-OOC history contaminate the next turns, and does it recover?
Conversation-level bootstrap (48 conversations, 2 samples each)."""
import json, argparse, collections, random, re, statistics as S

ap = argparse.ArgumentParser()
ap.add_argument("--tag", default="q8")
ap.add_argument("--dir", default="/home/xiang/rp_persona/runs/e0b")
ap.add_argument("--out", default=None)
args = ap.parse_args()

AST = re.compile(r"(let me know|feel free|hope (this|that) helps|happy to help|glad to help|anything else|"
                 r"if you('d| would) like|as an ai|here to help|assist you|i can help|certainly[,!.]|of course[,!.] )", re.I)
roll = {(r["id"], r["cond"], r["sample"], r["step"]): r for r in map(json.loads, open(f"{args.dir}/roll_{args.tag}.jsonl"))}
try:
    jud = {(r["id"], r["cond"], r["sample"], r["step"]): r for r in map(json.loads, open(f"{args.dir}/roll_{args.tag}.judge.jsonl"))}
except FileNotFoundError:
    jud = {}

M = {}
for k, r in roll.items():
    m = {"ast_phrase": float(bool(AST.search(r["visible"]))), "has_action": float(bool(r["actions"])),
         "has_rthink": float(bool(r["role_thinking"])), "words": len(r["visible"].split()),
         "dir_words": len(r["director"].split())}
    j = jud.get(k, {})
    for f in ("persona", "natural", "assistant", "ooc"):
        if isinstance(j.get(f), (int, float)):
            m["j_" + f] = float(j[f])
    M[k] = m

conds = ["gold", "para", "ooc", "ooc_anchor"]
steps = sorted({k[3] for k in M})
convs = sorted({k[0] for k in M})
rng = random.Random(0)
out = []
P = lambda *a: out.append(" ".join(str(x) for x in a))


def cell(cond, step, f, B=1000):
    per = {}
    for (i, c, s, t), m in M.items():
        if c == cond and t == step and f in m:
            per.setdefault(i, []).append(m[f])
    v = [S.mean(x) for x in per.values()]
    if not v:
        return "-"
    bs = sorted(S.mean(rng.choice(v) for _ in v) for _ in range(B))
    return f"{S.mean(v):.2f} [{bs[25]:.2f},{bs[975]:.2f}]"


def paired(c1, c2, step, f, B=2000):
    d = []
    for i in convs:
        a = [M[(i, c1, s, step)][f] for s in range(4) if (i, c1, s, step) in M and f in M[(i, c1, s, step)]]
        b = [M[(i, c2, s, step)][f] for s in range(4) if (i, c2, s, step) in M and f in M[(i, c2, s, step)]]
        if a and b:
            d.append(S.mean(a) - S.mean(b))
    if not d:
        return "-"
    bs = sorted(S.mean(rng.choice(d) for _ in d) for _ in range(B))
    return f"{S.mean(d):+.2f} [{bs[int(.025 * B)]:+.2f},{bs[int(.975 * B)]:+.2f}]"


fields = ["j_persona", "j_natural", "j_assistant", "j_ooc", "ast_phrase", "has_action", "has_rthink", "words"]
P(f"## E0-B ({args.tag}); {len(convs)} conversations; conversation-bootstrap 95% CI")
for t in steps:
    P(f"\n### step {t} (step 0 = first turn after the manipulated history)")
    P("cond | " + " | ".join(fields))
    for c in conds:
        P(c + " | " + " | ".join(cell(c, t, f) for f in fields))
P("\n## Paired differences")
for t in steps:
    for c1, c2 in [("ooc", "gold"), ("ooc", "para"), ("para", "gold"), ("ooc_anchor", "ooc")]:
        P(f"step {t} {c1}-{c2}: " + " | ".join(f"{f} {paired(c1, c2, t, f)}" for f in
                                               ["j_persona", "j_assistant", "ast_phrase", "has_action", "words"]))
text = "\n".join(out)
print(text)
if args.out:
    open(args.out, "w").write(text + "\n")
