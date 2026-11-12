"""Analyse slice 1.

p_pos = P(pos-pole letter) / (P(A) + P(B)), averaged over the two option orders.
Per family, mode, form:
  sens_self  = p_pos(pos, self)  - p_pos(neg, self)    should be large (role uses its own attitude/experience)
  sens_other = p_pos(pos, other) - p_pos(neg, other)   should be ~0  (another character's attitude/experience)
  default    = p_pos(none)
95% CIs: bootstrap over the 24 families.

usage: analyze_s1.py PROMPTS.jsonl RUN1.jsonl [RUN2.jsonl ...]
"""
import json
import math
import random
import sys
from collections import defaultdict
from itertools import product

MODES = ["K", "P", "EU", "ES"]


def boot(xs, n=2000, seed=0):
    rng = random.Random(seed)
    m = sum(xs) / len(xs)
    bs = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(n))
    return m, bs[int(0.025 * n)], bs[int(0.975 * n)]


def fmt(t):
    return f"{t[0]:+.2f} [{t[1]:+.2f},{t[2]:+.2f}]"


def load(prompts, run):
    meta = {}
    for l in open(prompts):
        r = json.loads(l)
        r.pop("messages")
        meta[r["id"]] = r
    cells = defaultdict(list)  # key without option order -> list of p_pos
    bad = 0
    mass = []
    for l in open(run):
        o = json.loads(l)
        m = meta[o["id"]]
        a, b = o["lpA"], o["lpB"]
        if a == -math.inf and b == -math.inf:
            bad += 1
            continue
        pa, pb = math.exp(a), math.exp(b)
        mass.append(pa + pb)
        p_pos = (pa if m["pos_letter"] == "A" else pb) / (pa + pb)
        key = (m["family"], m["kind"], m["valence"], m["owner"], m["form"], m["blocks"], m["mode"], m["para"])
        cells[key].append(p_pos)
    cells = {k: sum(v) / len(v) for k, v in cells.items()}
    return cells, bad, sum(mass) / len(mass)


def get(cells, fam, v, o, f, mode, blocks=None, para=None):
    vals = [p for (fa, _, va, ow, fo, bl, mo, pa), p in cells.items()
            if fa == fam and va == v and ow == o and fo == f and mo == mode
            and (blocks is None or bl == blocks) and (para is None or pa == para)]
    return sum(vals) / len(vals)


def report(tag, cells, bad, mass):
    fams = sorted({k[0] for k in cells})
    kind = {k[0]: k[1] for k in cells}
    print(f"\n######## {tag}   (unparsed rows: {bad}, mean A+B mass: {mass:.3f})")
    print("mode form    | sens_self              | sens_other             | default p_pos")
    for mode, form in product(MODES, ["stated", "exp"]):
        ss = [get(cells, f, "pos", "self", form, mode) - get(cells, f, "neg", "self", form, mode) for f in fams]
        so = [get(cells, f, "pos", "other", form, mode) - get(cells, f, "neg", "other", form, mode) for f in fams]
        d = [get(cells, f, "none", "none", "none", mode) for f in fams]
        print(f"{mode:3s}  {form:6s}  | {fmt(boot(ss))} | {fmt(boot(so))} | {sum(d)/len(d):.2f}")
    # by kind, experience form only
    print("  experience form, by family kind (sens_self / sens_other):")
    for k in ("trust", "pref"):
        fk = [f for f in fams if kind[f] == k]
        row = []
        for mode in MODES:
            ss = sum(get(cells, f, "pos", "self", "exp", mode) - get(cells, f, "neg", "self", "exp", mode) for f in fk) / len(fk)
            so = sum(get(cells, f, "pos", "other", "exp", mode) - get(cells, f, "neg", "other", "exp", mode) for f in fk) / len(fk)
            row.append(f"{mode} {ss:+.2f}/{so:+.2f}")
        print(f"    {k:5s}: " + "  ".join(row))
    # robustness: per wording and per block order
    print("  sens_self (exp) by wording para0 / para1, and by block order role-first / other-first:")
    for mode in MODES:
        p0 = sum(get(cells, f, "pos", "self", "exp", mode, para=0) - get(cells, f, "neg", "self", "exp", mode, para=0) for f in fams) / len(fams)
        p1 = sum(get(cells, f, "pos", "self", "exp", mode, para=1) - get(cells, f, "neg", "self", "exp", mode, para=1) for f in fams) / len(fams)
        b0 = sum(get(cells, f, "pos", "self", "exp", mode, blocks="role") - get(cells, f, "neg", "self", "exp", mode, blocks="role") for f in fams) / len(fams)
        b1 = sum(get(cells, f, "pos", "self", "exp", mode, blocks="other") - get(cells, f, "neg", "self", "exp", mode, blocks="other") for f in fams) / len(fams)
        o0 = sum(get(cells, f, "pos", "other", "exp", mode, para=0) - get(cells, f, "neg", "other", "exp", mode, para=0) for f in fams) / len(fams)
        o1 = sum(get(cells, f, "pos", "other", "exp", mode, para=1) - get(cells, f, "neg", "other", "exp", mode, para=1) for f in fams) / len(fams)
        print(f"    {mode:3s} self {p0:+.2f}/{p1:+.2f}  blocks {b0:+.2f}/{b1:+.2f}   other {o0:+.2f}/{o1:+.2f}")
    # role-consistency when the role's attitude agrees vs conflicts with the model's default (self, both forms)
    print("  P(role-consistent choice), self-owned, split by agreement with the default (none) choice:")
    for form in ("stated", "exp"):
        row = []
        for mode in MODES:
            agree, conflict = [], []
            for f in fams:
                d = get(cells, f, "none", "none", "none", mode)
                for v in ("pos", "neg"):
                    p = get(cells, f, v, "self", form, mode)
                    rc = p if v == "pos" else 1 - p
                    default_pole = "pos" if d > 0.5 else "neg"
                    (agree if v == default_pole else conflict).append(rc)
            row.append(f"{mode} {sum(agree)/len(agree):.2f}/{sum(conflict)/len(conflict):.2f}")
        print(f"    {form:6s} (agree/conflict): " + "  ".join(row))
    # joint K / P / E correctness pattern on experience-form, self-owned items
    print("  K/P/EU/ES correctness pattern, experience form, self-owned (per family x valence x blocks x wording):")
    pat = defaultdict(int)
    for f in fams:
        for v, bl, pa in product(("pos", "neg"), ("role", "other"), (0, 1)):
            bits = []
            for mode in MODES:
                p = get(cells, f, v, "self", "exp", mode, blocks=bl, para=pa)
                bits.append("1" if ((p > 0.5) if v == "pos" else (p < 0.5)) else "0")
            pat["".join(bits)] += 1
    tot = sum(pat.values())
    print("    " + "  ".join(f"{k}:{c/tot:.2f}" for k, c in sorted(pat.items(), key=lambda x: -x[1])))


if __name__ == "__main__":
    prompts = sys.argv[1]
    for run in sys.argv[2:]:
        cells, bad, mass = load(prompts, run)
        report(run.split("/")[-1].replace(".jsonl", ""), cells, bad, mass)
