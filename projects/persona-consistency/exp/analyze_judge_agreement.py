"""Cross-family judge check: Qwen3-32B vs Mistral-Small-24B on the same rows.

Per label: raw agreement, Cohen's kappa, base rates. Then recomputes the headline effects with each judge:
E0-C depth effect per probe (failure rate by depth) and E0-D condition rates at depth 20.
"""
import json, argparse, collections, statistics as S

ap = argparse.ArgumentParser()
ap.add_argument("--files", nargs="+", default=["/home/xiang/rp_persona/runs/e0c/e0c_q8her.jsonl",
                                               "/home/xiang/rp_persona/runs/e0d/e0d_q8her_d20.jsonl",
                                               "/home/xiang/rp_persona/runs/e0d/e0d_q8her_d2.jsonl"])
ap.add_argument("--valid", default="/home/xiang/rp_persona/data/e0c_probes_v2_validated.jsonl")
ap.add_argument("--out", default=None)
args = ap.parse_args()

FAIL = {"false_premise": "accepted_false", "pressure": "caved", "meta_ai": "revealed_ai",
        "true_premise": "rejected_true", "assistant_task": "complied"}
valid = {p["id"]: p for p in map(json.loads, open(args.valid))}
out = []
P = lambda *a: out.append(" ".join(str(x) for x in a))


def kappa(pairs):
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    pa, pb = sum(a for a, _ in pairs) / n, sum(b for _, b in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return po, (po - pe) / (1 - pe) if pe < 1 else float("nan"), pa, pb


key = lambda r: (r["id"], r["policy"], r["kind"], r["turn"], r["depth"], r["probe"], r["sample"])
rows = []
for f in args.files:
    q = {key(r): r["j"] for r in map(json.loads, open(f.replace(".jsonl", ".judge.jsonl")))}
    m = {key(r): r["j"] for r in map(json.loads, open(f.replace(".jsonl", ".judge_mistral.jsonl")))}
    for k in q:
        if k in m and "parse_error" not in q[k] and "parse_error" not in m[k]:
            rows.append((f, k, q[k], m[k]))
P(f"rows judged by both: {len(rows)}")

P("\n## Agreement per label (probe rows; label = probe-specific failure, plus in_character on all rows)")
for probe, lab in FAIL.items():
    pairs = [(int(q.get(lab) == 1), int(m.get(lab) == 1)) for f, k, q, m in rows if k[2] == "probe" and k[5] == probe
             and lab in q and lab in m]
    if pairs:
        po, kp, pa, pb = kappa(pairs)
        P(f"{lab:15s} n={len(pairs):4d} agree={po:.2f} kappa={kp:.2f} rate qwen={pa:.2f} mistral={pb:.2f}")
pairs = [(int(q.get("in_character", 1) == 0), int(m.get("in_character", 1) == 0)) for f, k, q, m in rows]
po, kp, pa, pb = kappa(pairs)
P(f"{'out_of_char':15s} n={len(pairs):4d} agree={po:.2f} kappa={kp:.2f} rate qwen={pa:.2f} mistral={pb:.2f}")


def rate(sel, j_index, lab, only_valid=True):
    v = [int(x[j_index].get(lab) == 1) for x in sel
         if not only_valid or valid[x[1][0]].get("false_valid", True) or x[1][5] != "false_premise"]
    return (sum(v) / len(v), len(v)) if v else (float("nan"), 0)


P("\n## E0-C depth effect (Qwen3-8B her) with each judge; false_premise restricted to validated probes")
for probe in ("false_premise", "meta_ai", "pressure", "assistant_task"):
    cells = []
    for d in (2, 10, 20):
        sel = [x for x in rows if x[0].endswith("e0c_q8her.jsonl") and x[1][2] == "probe" and x[1][5] == probe and x[1][4] == d]
        rq, n = rate(sel, 2, FAIL[probe]); rm, _ = rate(sel, 3, FAIL[probe])
        cells.append(f"d{d}: qwen {rq:.2f} / mistral {rm:.2f} (n={n})")
    P(f"{probe}: " + " | ".join(cells))

P("\n## E0-D false_premise at depth 20 (validated probes) with each judge")
for cond in ("full", "trunc2", "reanchor", "generic_dir", "oracle_dir"):
    sel = [x for x in rows if x[0].endswith("e0d_q8her_d20.jsonl") and x[1][1] == cond and x[1][5] == "false_premise"]
    rq, n = rate(sel, 2, "accepted_false"); rm, _ = rate(sel, 3, "accepted_false")
    P(f"{cond:12s}: qwen {rq:.2f} / mistral {rm:.2f} (n={n})")
sel = [x for x in rows if x[0].endswith("e0d_q8her_d2.jsonl") and x[1][1] == "full" and x[1][5] == "false_premise"]
rq, n = rate(sel, 2, "accepted_false"); rm, _ = rate(sel, 3, "accepted_false")
P(f"{'full@d2':12s}: qwen {rq:.2f} / mistral {rm:.2f} (n={n})")
text = "\n".join(out)
print(text)
if args.out:
    open(args.out, "w").write(text + "\n")
