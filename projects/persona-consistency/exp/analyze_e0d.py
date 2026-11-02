"""Probe-level analysis for E0-D / E0-E style runs: failure rates per condition@depth, paired contrasts.

failure = out of character OR the probe-specific failure; "none" probes report generic and persona.
--valid restricts premise probes to those validated against the setup (validate_probes.py).
"""
import json, argparse, collections, random, statistics as S

ap = argparse.ArgumentParser()
ap.add_argument("--files", nargs="+", default=["/home/xiang/rp_persona/runs/e0d/e0d_q8her_d20.jsonl",
                                               "/home/xiang/rp_persona/runs/e0d/e0d_q8her_d2.jsonl"])
ap.add_argument("--conds", default="full@d2,full@d20,trunc2@d20,reanchor@d20,generic_dir@d20,oracle_dir@d20")
ap.add_argument("--base", default="full@d20")
ap.add_argument("--valid", default=None, help="validated probes file; keep only valid premise probes")
ap.add_argument("--out", default=None)
args = ap.parse_args()

FAIL = {"false_premise": "accepted_false", "pressure": "caved", "meta_ai": "revealed_ai",
        "true_premise": "rejected_true", "assistant_task": "complied"}
valid = {}
if args.valid:
    for p in map(json.loads, open(args.valid)):
        valid[p["id"]] = {"false_premise": p.get("false_valid", True), "true_premise": p.get("true_valid", True)}

rows = []
for f in args.files:
    for r in map(json.loads, open(f.replace(".jsonl", ".judge.jsonl"))):
        j = r["j"]
        if "parse_error" in j or not valid.get(r["id"], {}).get(r["probe"], True):
            continue
        spec = float(j.get(FAIL[r["probe"]]) == 1) if r["probe"] in FAIL else float("nan")
        inc = float(j.get("in_character", 1))
        rows.append({"id": r["id"], "cond": f"{r['policy']}@d{r['depth']}", "probe": r["probe"], "spec": spec,
                     "inc": inc, "any": float(inc == 0 or spec == 1), "generic": float(j.get("generic", 0)),
                     "persona": float(j.get("persona", 0))})

rng = random.Random(0)
out = []
P = lambda *a: out.append(" ".join(str(x) for x in a))
conds = args.conds.split(",")


def per_conv(cond, probe, k):
    d = collections.defaultdict(list)
    for r in rows:
        if r["cond"] == cond and r["probe"] == probe:
            d[r["id"]].append(r[k])
    return {cid: S.mean(v) for cid, v in d.items()}


def ci(v, B=2000):
    bs = sorted(S.mean(rng.choice(v) for _ in v) for _ in range(B))
    return f"{S.mean(v):.2f} [{bs[int(.025 * B)]:.2f},{bs[int(.975 * B)]:.2f}]"


for probe in sorted({r["probe"] for r in rows}, key=lambda p: list(FAIL).index(p) if p in FAIL else 9):
    keys = ["any", "inc", "persona", "generic"] if probe == "none" else ["spec", "inc", "any", "persona"]
    P(f"\n## {probe}: " + " | ".join(keys))
    for c in conds:
        m = [per_conv(c, probe, k) for k in keys]
        if m[0]:
            P(f"{c}: " + " | ".join(ci(list(x.values())) for x in m) + f"  (n_conv={len(m[0])})")
    for k in (["any", "persona"] if probe == "none" else ["any", "persona"]):
        base = per_conv(args.base, probe, k)
        for c in conds:
            if c == args.base:
                continue
            other = per_conv(c, probe, k)
            d = [other[x] - base[x] for x in base if x in other]
            if d:
                P(f"  {k}: {c} - {args.base} (paired): {ci(d)}")
text = "\n".join(out)
print(text)
if args.out:
    open(args.out, "w").write(text + "\n")
