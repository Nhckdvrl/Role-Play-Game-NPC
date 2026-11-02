"""One table across training rounds: closed loop D20, natural persona drift, held-out styles, benign evasion,
hostility (from log), APC single-turn fact use (paired by item vs base). Conversation/item-level bootstrap.

--rounds name:closed_tag:heldout_file:benign_file:apc_tag  (benign_file may be '-' if benign_q lives in heldout_file)
"""
import json, argparse, collections, random, statistics as S

ap = argparse.ArgumentParser()
ap.add_argument("--rounds", required=True)
ap.add_argument("--valid", default="/home/xiang/rp_persona/data/e0c_probes_heldout.jsonl")
ap.add_argument("--judge_suffix", default="judge")
args = ap.parse_args()
R = "/home/xiang/rp_persona/runs"
FAIL = {"assistant_task": "complied", "false_premise": "accepted_false", "pressure": "caved", "meta_ai": "revealed_ai",
        "false_q": "accepted_false", "meta_p1": "revealed_ai", "meta_p2": "revealed_ai", "meta_p3": "revealed_ai",
        "benign_q": "evasive"}
V = {r["id"]: r for r in map(json.loads, open(args.valid))}
rng = random.Random(0)


def load(path):
    try:
        return [json.loads(l) for l in open(path)]
    except FileNotFoundError:
        return []


def boot(per, B=1000):
    v = [S.mean(x) for x in per.values() if x]
    if not v:
        return float("nan"), "-"
    bs = sorted(S.mean(rng.choice(v) for _ in v) for _ in range(B))
    return S.mean(v), f"{S.mean(v):.3f} [{bs[25]:.3f},{bs[975]:.3f}]"


def rate(rows, probes, depth=None):
    per = collections.defaultdict(list)
    for r in rows:
        p = r["probe"]
        if r["kind"] != "probe" or p not in probes or (depth and r["depth"] != depth):
            continue
        if p == "false_premise" and not V[r["id"]]["false_valid"] or p == "false_q" and not V[r["id"]]["false_q_valid"]:
            continue
        x = r["j"].get(FAIL[p])
        if isinstance(x, (int, float)):
            per[r["id"]].append(float(x))
    return boot(per)[1]


def apc(tag):
    out = {}
    for r in load(f"{R}/e0a/gen_srv_{tag}.apc.jsonl"):
        act = [s for s in r["stmts"] if s["gold"]]               # act_entail, as in the logged APC tables
        if not act:
            continue
        v = S.mean(float(s["visible"][1] > 0.5) for s in act)
        out.setdefault(r["cond"], {}).setdefault(r["id"], []).append(v)
    return out


base_apc = None
for spec in args.rounds.split(","):
    name, ct, hf, bf, at = spec.split(":")
    print(f"\n### {name}")
    cl = load(f"{R}/e0c/e0c_{ct}.{args.judge_suffix}.jsonl")
    for p in ("false_premise", "meta_ai", "pressure", "assistant_task"):
        print(f"closed D20 {p}: {rate(cl, {p}, 20)}")
    for lo, hi in ((0, 4), (15, 19)):
        per = collections.defaultdict(list)
        for r in cl:
            if r["kind"] == "natural" and lo <= r["turn"] <= hi and isinstance(r["j"].get("persona"), (int, float)):
                per[r["id"]].append(float(r["j"]["persona"]))
        print(f"natural persona t{lo}-{hi}: {boot(per)[1]}")
    ho = load(f"{R}/e1/{hf}.{args.judge_suffix}.jsonl")
    print(f"heldout false_q: {rate(ho, {'false_q'})} | meta_p*: {rate(ho, {'meta_p1', 'meta_p2', 'meta_p3'})}")
    bn = ho if bf == "-" else load(f"{R}/e1/{bf}.{args.judge_suffix}.jsonl")
    print(f"benign_q evasive: {rate(bn, {'benign_q'})}")
    a = apc(at)
    if base_apc is None:
        base_apc = a
    for c in ("her_self", "direct"):
        per = {i: v for i, v in a.get(c, {}).items()}
        line = f"APC {c}: {boot(per)[1]}"
        if a is not base_apc:
            d = {i: [S.mean(v) - S.mean(base_apc[c][i])] for i, v in per.items() if i in base_apc.get(c, {})}
            line += f" | paired diff vs base {boot(d)[1]}"
        print(line)
