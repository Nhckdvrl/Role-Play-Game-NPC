"""S10: attitude effect in decisions with no cost sentence, vs v2 (cost-counterbalanced).
usage: analyze_s10.py TAG"""
import sys
from analyze_s2 import Q, load
tag = sys.argv[1]
q10 = Q(load("/home/xiang/rp_mech/s10/data/prompts.jsonl", f"/home/xiang/rp_mech/s10/runs/{tag}.jsonl")[0])
c2, kind, _ = load("/home/xiang/rp_mech/s2/data/prompts.jsonl", f"/home/xiang/rp_mech/s2/runs/{tag}.jsonl"); q2 = Q(c2)
fams = sorted(kind)
def s(q, o, f, conv):
    return sum(q.sens(fa, o, f, m, conv=conv) for fa in fams for m in ("P", "EU")) / (2 * len(fams))
print(f"{tag:12s} K self exp {sum(q2.sens(fa,'self','exp','K') for fa in fams)/len(fams):+.2f} | no cost: self exp {s(q10,'self','exp','nocost'):+.2f} stated {s(q10,'self','stated','nocost'):+.2f} other {s(q10,'other','exp','nocost'):+.2f} world {s(q10,'world','exp','nocost'):+.2f} | with cost (v2): self exp {s(q2,'self','exp',None):+.2f} stated {s(q2,'self','stated',None):+.2f} | none p_pos nocost {sum(q10.p(fa,'none','none','none',m,conv='nocost') for fa in fams for m in ('P','EU'))/(2*len(fams)):.2f}")
