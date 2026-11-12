"""Compact K-vs-decision summary across Qwen3 sizes on v2 prompts.
usage: scale_summary.py RUN1.jsonl [RUN2 ...]   (tag taken from filename)"""
import sys
from analyze_s2 import Q, load
P = "/home/xiang/rp_mech/s2/data/prompts.jsonl"
print(f"{'model':12s} {'K self exp':>10s} {'K self st':>9s} {'K world':>8s} | {'dec self exp':>12s} {'dec stated':>10s} {'dec world':>9s} {'dec other':>9s} {'conv wt':>8s}")
for run in sys.argv[1:]:
    cells, kind, bad = load(P, run)
    q = Q(cells); fams = sorted(kind); D = ["P", "EU", "ES"]
    m = lambda f: sum(f(x) for x in fams) / len(fams)
    ks = m(lambda x: q.sens(x, "self", "exp", "K")); kst = m(lambda x: q.sens(x, "self", "stated", "K")); kw = m(lambda x: q.sens(x, "world", "exp", "K"))
    de = m(lambda x: sum(q.sens(x, "self", "exp", d) for d in D) / 3); ds = m(lambda x: sum(q.sens(x, "self", "stated", d) for d in D) / 3)
    dw = m(lambda x: sum(q.sens(x, "world", "exp", d) for d in D) / 3); do = m(lambda x: sum(q.sens(x, "other", "exp", d) for d in D) / 3)
    cw = m(lambda x: sum(q.p(x, "none", "none", "none", d, conv="neg_costly") - q.p(x, "none", "none", "none", d, conv="pos_costly") for d in D) / 3)
    print(f"{run.split('/')[-1][:-6]:12s} {ks:+10.2f} {kst:+9.2f} {kw:+8.2f} | {de:+12.2f} {ds:+10.2f} {dw:+9.2f} {do:+9.2f} {cw:+8.2f}")
