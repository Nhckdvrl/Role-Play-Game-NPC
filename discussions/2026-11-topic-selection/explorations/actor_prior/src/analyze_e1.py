"""E1 analysis: P(role option) by model x condition, persona leverage, robustness.

P(role) per prompt = softmax over {A,B} next-token log-probs, mapped to the role letter,
then averaged over the two option orders (removes position bias). Reported per paraphrase
and pooled; CIs by bootstrap over personas.
"""
import collections
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path.home() / "rp_prior"
prompts = {r["id"]: r for r in map(json.loads, open(ROOT / "data/e1_prompts.jsonl"))}
ORDER = ["olmo2_base", "olmo2_sft", "olmo2_dpo", "olmo2_inst", "llama31_base", "tulu3_sft", "tulu3_dpo", "tulu3",
         "llama31_8b_inst", "coser_8b", "qwen3_8b_base", "qwen3_8b", "arcane_8b"]


def p_role(r, lpA, lpB):
    if lpA == -math.inf and lpB == -math.inf:
        return None
    a, b = math.exp(lpA) if lpA > -1e9 else 0.0, math.exp(lpB) if lpB > -1e9 else 0.0
    pa = a / (a + b)
    return pa if r["role_letter"] == "A" else 1 - pa


def logit(p, eps=1e-3):
    p = min(max(p, eps), 1 - eps)
    return math.log(p / (1 - p))


def boot(vals, n=1000):
    v = np.array(vals)
    rng = np.random.default_rng(0)
    b = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(n)]
    return v.mean(), np.percentile(b, 2.5), np.percentile(b, 97.5)


def main():
    data = collections.defaultdict(dict)  # model -> id -> p_role
    cover = {}
    for f in sorted((ROOT / "runs/e1").glob("*.jsonl")):
        tag = f.stem
        n = ok = 0
        for g in map(json.loads, open(f)):
            n += 1
            p = p_role(prompts[g["id"]], g["lpA"], g["lpB"])
            if p is not None:
                ok += 1
                data[tag][g["id"]] = p
        cover[tag] = ok / max(n, 1)
    models = [m for m in ORDER if m in data] + sorted(m for m in data if m not in ORDER)
    print("A/B token coverage:", {m: round(cover[m], 3) for m in models})
    # cell = (pid, diff, cond, para): average over swap
    for m in models:
        cells = collections.defaultdict(list)
        for i, p in data[m].items():
            r = prompts[i]
            cells[(r["pid"], r["diff"], r["cond"], r["para"])].append(p)
        cell = {k: np.mean(v) for k, v in cells.items() if len(v) == 2}
        data[m] = cell
    print("\nP(role option), pooled over paraphrases & difficulty  [none | identity | value]   leverage(value-none, logit)")
    for m in models:
        c = data[m]
        row = []
        for cond in ("none", "identity", "value"):
            v = [p for k, p in c.items() if k[2] == cond]
            row.append(f"{np.mean(v):.3f}")
        lev = [logit(c[(pid, d, "value", pa)]) - logit(c[(pid, d, "none", pa)])
               for (pid, d, cond, pa) in c if cond == "value" and (pid, d, "none", pa) in c]
        mu, lo, hi = boot(lev)
        print(f"  {m:16s} {' | '.join(row)}   lev {mu:+.2f} [{lo:+.2f},{hi:+.2f}]")
    print("\nby paraphrase (value - none, P scale)")
    for m in models:
        c = data[m]
        s = []
        for pa in (0, 1):
            dv = [c[(pid, d, 'value', pa)] - c[(pid, d, 'none', pa)] for (pid, d, cond, p2) in c
                  if cond == "value" and p2 == pa and (pid, d, "none", pa) in c]
            s.append(f"p{pa}: {np.mean(dv):+.3f}")
        print(f"  {m:16s} {'  '.join(s)}")
    print("\nby difficulty: P(role) none -> value")
    for m in models:
        c = data[m]
        s = []
        for d in ("easy", "mid", "hard"):
            n0 = np.mean([p for k, p in c.items() if k[1] == d and k[2] == "none"])
            n2 = np.mean([p for k, p in c.items() if k[1] == d and k[2] == "value"])
            s.append(f"{d}: {n0:.2f}->{n2:.2f}")
        print(f"  {m:16s} {'  '.join(s)}")


if __name__ == "__main__":
    main()
