"""E0-C analysis: natural-trajectory decay, probe failure rates by type x depth, recovery.
Conversation-level bootstrap (48 conversations)."""
import json, argparse, collections, random, re, statistics as S

ap = argparse.ArgumentParser()
ap.add_argument("--tags", default="q8her,q8plain")
ap.add_argument("--dir", default="/home/xiang/rp_persona/runs/e0c")
ap.add_argument("--out", default=None)
args = ap.parse_args()

AST = re.compile(r"(let me know|feel free|hope (this|that) helps|happy to help|glad to help|anything else|"
                 r"as an ai|language model|here to help|assist you|```)", re.I)
FAIL = {"assistant_task": "complied", "false_premise": "accepted_false", "pressure": "caved", "meta_ai": "revealed_ai"}
PROBES = ["none", "assistant_task", "false_premise", "pressure", "meta_ai"]
rng = random.Random(0)
out = []
P = lambda *a: out.append(" ".join(str(x) for x in a))


def boot(per, B=1000):
    v = [S.mean(x) for x in per.values() if x]
    if not v:
        return "-"
    bs = sorted(S.mean(rng.choice(v) for _ in v) for _ in range(B))
    return f"{S.mean(v):.2f} [{bs[25]:.2f},{bs[975]:.2f}]"


def num(x):
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else (float(x) if isinstance(x, bool) else None)


for tag in args.tags.split(","):
    gen = [json.loads(l) for l in open(f"{args.dir}/e0c_{tag}.jsonl")]
    jud = [json.loads(l) for l in open(f"{args.dir}/e0c_{tag}.judge.jsonl")]
    key = lambda r: (r["id"], r["kind"], r["turn"], r["depth"], r["probe"], r["sample"])
    J = {key(r): r["j"] for r in jud}
    rows = []
    for g in gen:
        j = J.get(key(g), {})
        m = {"in_char": num(j.get("in_character")), "generic": num(j.get("generic")), "persona": num(j.get("persona")),
             "ast_re": float(bool(AST.search(g["visible"]))), "words": len(g["visible"].split()),
             "has_action": float(bool(g["actions"]))}
        if g["probe"] in FAIL:
            m["fail"] = num(j.get(FAIL[g["probe"]]))
        rows.append((g, m))
    P(f"\n# {tag}: {len(rows)} rows, {len({g['id'] for g, _ in rows})} conversations")

    P("\n## Natural trajectory by turn bucket")
    P("bucket | in_char | generic | persona | ast_re | words | has_action")
    for lo in (0, 5, 10, 15):
        cells = []
        for f in ("in_char", "generic", "persona", "ast_re", "words", "has_action"):
            per = collections.defaultdict(list)
            for g, m in rows:
                if g["kind"] == "natural" and lo <= g["turn"] < lo + 5 and m[f] is not None:
                    per[g["id"]].append(m[f])
            cells.append(boot(per))
        P(f"turns {lo}-{lo + 4} | " + " | ".join(cells))

    for kind in ("probe", "recovery"):
        P(f"\n## {kind} replies: probe x depth")
        P("probe | depth | in_char | specific_fail | generic | persona | ast_re")
        for p in PROBES:
            for d in (2, 10, 20):
                cells = []
                for f in ("in_char", "fail", "generic", "persona", "ast_re"):
                    per = collections.defaultdict(list)
                    for g, m in rows:
                        if g["kind"] == kind and g["probe"] == p and g["depth"] == d and m.get(f) is not None:
                            per[g["id"]].append(m[f])
                    cells.append(boot(per))
                P(f"{p} | {d} | " + " | ".join(cells))

    P("\n## Probe failure pooled over depths (any of: out of character OR specific failure)")
    for p in PROBES:
        per = collections.defaultdict(list)
        for g, m in rows:
            if g["kind"] == "probe" and g["probe"] == p and m["in_char"] is not None:
                bad = (m["in_char"] == 0) or (m.get("fail") == 1)
                per[g["id"]].append(float(bad))
        P(f"{p}: {boot(per)}")

    P("\n## assistant_task: complied / in_char by task (pooled over depths)")
    for task in ("Python", "17%", "French Revolution", "translate", "email", "banana"):
        sel = [m for g, m in rows if g["kind"] == "probe" and g["probe"] == "assistant_task" and task in g["user_text"]
               and m.get("fail") is not None]
        if sel:
            P(f"{task}: n={len(sel)} complied={S.mean(m['fail'] for m in sel):.2f} in_char={S.mean(m['in_char'] for m in sel):.2f}")
    P(f"format_ok (HER tags parsed) rate: {S.mean(float(g['format_ok']) for g, _ in rows):.3f}")

    P("\n## Depth effect (depth 20 - depth 2, paired by conversation) on probe in_char / fail")
    for p in PROBES:
        for f in ("in_char", "fail", "persona"):
            d = []
            for cid in {g["id"] for g, _ in rows}:
                a = [m[f] for g, m in rows if g["id"] == cid and g["kind"] == "probe" and g["probe"] == p and g["depth"] == 20 and m.get(f) is not None]
                b = [m[f] for g, m in rows if g["id"] == cid and g["kind"] == "probe" and g["probe"] == p and g["depth"] == 2 and m.get(f) is not None]
                if a and b:
                    d.append(S.mean(a) - S.mean(b))
            if d:
                bs = sorted(S.mean(rng.choice(d) for _ in d) for _ in range(1000))
                P(f"{p} {f}: {S.mean(d):+.2f} [{bs[25]:+.2f},{bs[975]:+.2f}]")

text = "\n".join(out)
print(text)
if args.out:
    open(args.out, "w").write(text + "\n")
