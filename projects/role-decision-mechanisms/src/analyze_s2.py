"""Analyse S1 v2 (convenience counterbalanced; world-event condition).

p_pos = P(pos-pole letter) / (P(A)+P(B)), averaged over option order.
Decision effects are averaged over the two cost arrangements, so the attitude pole is
convenient half the time (confound-free). Also reported per arrangement.

  sens(owner, form) = p_pos(pos) - p_pos(neg)       for owner in self / other / world
  conv_w            = p_pos(neg_costly) - p_pos(pos_costly), in the none condition (weight of convenience)
CIs: bootstrap over the 24 families.

usage: analyze_s2.py PROMPTS.jsonl RUN1.jsonl [RUN2.jsonl ...]
"""
import json
import math
import random
import sys
from collections import defaultdict
from itertools import product

DEC = ["P", "EU", "ES"]


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
    acc = defaultdict(list)
    bad = 0
    for l in open(run):
        o = json.loads(l)
        m = meta[o["id"]]
        a, b = o["lpA"], o["lpB"]
        if a == -math.inf and b == -math.inf:
            bad += 1
            continue
        pa, pb = math.exp(a), math.exp(b)
        acc[(m["family"], m["valence"], m["owner"], m["form"], m["conv"], m["mode"], m["para"])].append(
            (pa if m["pos_letter"] == "A" else pb) / (pa + pb))
    cells = {k: sum(v) / len(v) for k, v in acc.items()}
    kind = {m["family"]: m["kind"] for m in meta.values()}
    return cells, kind, bad


class Q:
    def __init__(self, cells):
        self.c = cells
        self.idx = defaultdict(list)
        for (fa, v, o, f, cv, mo, pa), p in cells.items():
            self.idx[(fa, v, o, f, cv, mo)].append((pa, p))

    def p(self, fam, v, o, f, mode, conv=None, para=None):
        convs = [conv] if conv else (["na"] if mode == "K" else ["pos_costly", "neg_costly"])
        vals = [p for cv in convs for pa, p in self.idx[(fam, v, o, f, cv, mode)] if para is None or pa == para]
        return sum(vals) / len(vals)

    def sens(self, fam, o, f, mode, **kw):
        return self.p(fam, "pos", o, f, mode, **kw) - self.p(fam, "neg", o, f, mode, **kw)


def report(tag, cells, kind, bad):
    q = Q(cells)
    fams = sorted(kind)
    print(f"\n######## {tag}   (unparsed rows: {bad})")
    print("Attitude effect averaged over cost arrangement (sens = p_pos|pos - p_pos|neg):")
    print("mode form    | self                   | other                  | world (exp only)")
    for mode, form in product(["K"] + DEC, ["stated", "exp"]):
        s = boot([q.sens(f, "self", form, mode) for f in fams])
        o = boot([q.sens(f, "other", form, mode) for f in fams])
        w = fmt(boot([q.sens(f, "world", "exp", mode) for f in fams])) if form == "exp" else ""
        print(f"{mode:3s}  {form:6s}  | {fmt(s)} | {fmt(o)} | {w}")
    print("Convenience weight in the none condition, p_pos(neg_costly) - p_pos(pos_costly):")
    print("    " + "  ".join(f"{m} {fmt(boot([q.p(f,'none','none','none',m,conv='neg_costly') - q.p(f,'none','none','none',m,conv='pos_costly') for f in fams]))}" for m in DEC))
    print("Self-owned attitude effect split by cost arrangement (pos pole convenient / pos pole costly):")
    for form in ("stated", "exp"):
        row = []
        for m in DEC:
            a = sum(q.sens(f, "self", form, m, conv="neg_costly") for f in fams) / len(fams)
            b = sum(q.sens(f, "self", form, m, conv="pos_costly") for f in fams) / len(fams)
            row.append(f"{m} {a:+.2f}/{b:+.2f}")
        print(f"    {form:6s}: " + "  ".join(row))
    print("P(role-consistent choice), self-owned, when the role-consistent option is convenient / costly:")
    for form in ("stated", "exp"):
        row = []
        for m in DEC:
            conv_ok, conv_bad = [], []
            for f in fams:
                for v in ("pos", "neg"):
                    for cv in ("pos_costly", "neg_costly"):
                        p = q.p(f, v, "self", form, m, conv=cv)
                        rc = p if v == "pos" else 1 - p
                        costly = (v == "pos" and cv == "pos_costly") or (v == "neg" and cv == "neg_costly")
                        (conv_bad if costly else conv_ok).append(rc)
            row.append(f"{m} {sum(conv_ok)/len(conv_ok):.2f}/{sum(conv_bad)/len(conv_bad):.2f}")
        print(f"    {form:6s}: " + "  ".join(row))
    print("By family kind, experience form (self / other / world), decision modes pooled:")
    for k in ("trust", "pref"):
        fk = [f for f in fams if kind[f] == k]
        vals = [sum(q.sens(f, o, "exp", m) for f in fk for m in DEC) / (len(fk) * 3) for o in ("self", "other", "world")]
        kk = [sum(q.sens(f, o, "exp", "K") for f in fk) / len(fk) for o in ("self", "other", "world")]
        print(f"    {k:5s}: decision {vals[0]:+.2f} / {vals[1]:+.2f} / {vals[2]:+.2f}    K {kk[0]:+.2f} / {kk[1]:+.2f} / {kk[2]:+.2f}")
    print("Wording robustness (para0 / para1), experience form: self, other, world")
    for m in ["K"] + DEC:
        r = []
        for o in ("self", "other", "world"):
            a = sum(q.sens(f, o, "exp", m, para=0) for f in fams) / len(fams)
            b = sum(q.sens(f, o, "exp", m, para=1) for f in fams) / len(fams)
            r.append(f"{o} {a:+.2f}/{b:+.2f}")
        print(f"    {m:3s} " + "  ".join(r))
    print("K / P / EU / ES correctness pattern, experience form, self-owned (family x valence x cost x wording):")
    pat = defaultdict(int)
    for f, v, cv, pa in product(fams, ("pos", "neg"), ("pos_costly", "neg_costly"), (0, 1)):
        bits = []
        for m in ["K"] + DEC:
            p = q.p(f, v, "self", "exp", m, conv=("na" if m == "K" else cv), para=pa)
            bits.append("1" if ((p > 0.5) if v == "pos" else (p < 0.5)) else "0")
        pat["".join(bits)] += 1
    tot = sum(pat.values())
    print("    " + "  ".join(f"{k}:{c/tot:.2f}" for k, c in sorted(pat.items(), key=lambda x: -x[1])[:8]))


if __name__ == "__main__":
    for run in sys.argv[2:]:
        report(run.split("/")[-1].replace(".jsonl", ""), *load(sys.argv[1], run))
