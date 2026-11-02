"""P1 selectivity table: in-story AI challenge (revealed_ai, lower better) vs out-of-character sincere AI question
(honest_disclosure, higher better) and legitimate OOC request (honored, higher better). Conversation bootstrap,
paired differences vs base."""
import json, random, statistics as S, sys

R = "/home/xiang/rp_persona/runs/e1"
POL = sys.argv[1].split(",") if len(sys.argv) > 1 else ["base", "r1", "r2", "r2p", "r2p2"]
FIELD = {"meta_ai": "revealed_ai", "ooc_ai": "honest_disclosure", "ooc_req": "honored"}
rng = random.Random(0)


def fam(p):
    return p if p == "meta_ai" else p.rsplit("_", 1)[0]


def load(pol):
    d = {}
    for r in map(json.loads, open(f"{R}/p1_{pol}_d20.judge.jsonl")):
        f = fam(r["probe"])
        x = r["j"].get(FIELD[f])
        if isinstance(x, int):
            d.setdefault(f, {}).setdefault(r["id"], []).append(x)
    return d


def boot(v):
    bs = sorted(S.mean(rng.choice(v) for _ in v) for _ in range(2000))
    return f"{S.mean(v):.3f} [{bs[50]:.3f},{bs[1950]:.3f}]"


D = {p: load(p) for p in POL}
for f in FIELD:
    print(f"\n## {f} ({FIELD[f]})")
    for p in POL:
        per = D[p].get(f, {})
        line = f"{p}: {boot([S.mean(v) for v in per.values()])}"
        if p != "base":
            ids = [i for i in per if i in D["base"].get(f, {})]
            line += f" | vs base {boot([S.mean(per[i]) - S.mean(D['base'][f][i]) for i in ids])}"
        print(line)
