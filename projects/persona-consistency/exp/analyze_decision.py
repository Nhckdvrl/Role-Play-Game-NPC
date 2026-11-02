"""Pre-registered decision test (2026-11-02) under the validated judge (step-5, original rubric).
Stop this line if (1) the base D2->D20 increase in accepting false claims is not significant, or (2) the trained policies'
gain over base is not significant or less than half of what the original judge reported.
Also reports judge validity against both blind human label sets."""
import json, random, statistics as S, collections, sys

R = "/home/xiang/rp_persona"
SUF = sys.argv[1] if len(sys.argv) > 1 else "judge_step5"
valid = {json.loads(l)["id"]: json.loads(l)["false_valid"] for l in open(f"{R}/data/e0c_probes_heldout.jsonl")}
H1 = json.load(open(f"{R}/runs/audit/blind_human.json"))
H2 = json.load(open(f"{R}/runs/audit/blind2_human.json"))
BAD = {h["id"] for h in H1 + H2 if h["human"] == "N"}
rng = random.Random(0)


def load(tag, suf):
    out = {}
    for r in map(json.loads, open(f"{R}/runs/e0c/e0c_{tag}.{suf}.jsonl")):
        if r["kind"] == "probe" and r["probe"] == "false_premise" and isinstance(r["j"].get("accepted_false"), int):
            out[(r["id"], r["depth"], r["sample"])] = r["j"]["accepted_false"]
    return out


def per_conv(tags, suf, depth, excl_bad):
    per = collections.defaultdict(list)
    for t in tags:
        for (i, d, s), a in load(t, suf).items():
            if d == depth and valid.get(i) and not (excl_bad and i in BAD):
                per[i].append(a)
    return {i: S.mean(v) for i, v in per.items()}


def ci(v):
    bs = sorted(S.mean(rng.choice(v) for _ in v) for _ in range(4000))
    return f"{S.mean(v):+.3f} [{bs[100]:+.3f},{bs[3900]:+.3f}]"


BASE = ["q8her", "q8her_s1", "q8her_s2"]
for suf in ("judge", SUF):
    for excl in (False, True):
        print(f"\n### judge={suf} | {'excluding' if excl else 'including'} the {len(BAD)} human-flagged unclear probes")
        b = {d: per_conv(BASE, suf, d, excl) for d in (2, 10, 20)}
        print("base accept D2/D10/D20:", " / ".join(f"{S.mean(b[d].values()):.3f}" for d in (2, 10, 20)), f"(n_conv={len(b[20])})")
        ids = [i for i in b[2] if i in b[20]]
        print("  base D20 - D2 (paired by conversation):", ci([b[20][i] - b[2][i] for i in ids]))
        for t in ("r2p2_her", "r2pp_her"):
            for d in (2, 20):
                x = per_conv([t], suf, d, excl)
                ids = [i for i in x if i in b[d]]
                print(f"  {t} D{d}: {S.mean(x.values()):.3f} | minus base: {ci([x[i] - b[d][i] for i in ids])}")

print("\n### judge validity vs blind human labels (clear items only; A = accepts)")
for name, H in (("set1 (base, D2+D20)", H1), ("set2 (base/r2p2/r2pp, D20)", H2)):
    by = collections.defaultdict(lambda: collections.Counter())
    for h in H:
        if h["human"] not in "ACD":
            continue
        for suf in ("judge", SUF):
            a = load(h["tag"], suf).get((h["id"], h["depth"], h["sample"]))
            by[(suf, h["tag"])][(h["human"] == "A", a)] += 1
    for (suf, tag), c in sorted(by.items()):
        tp, fn, fp, tn = c[(True, 1)], c[(True, 0)], c[(False, 1)], c[(False, 0)]
        print(f"  {name:28s} {suf:12s} {tag:9s} recall {tp}/{tp + fn}  false-alarm {fp}/{fp + tn}")
