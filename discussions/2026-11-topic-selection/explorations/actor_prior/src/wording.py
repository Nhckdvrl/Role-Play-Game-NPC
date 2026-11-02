"""How often do RoleCDE option texts carry evaluative/self-condemning clauses, and does P(role) depend on it?"""
import collections, json, math, re, sys
from pathlib import Path
import numpy as np
ROOT = Path.home() / "rp_prior"
rows = json.load(open(ROOT / "data/rolecde_all.json"))
NEG = re.compile(r"\b(even if|even at|at the expense|despite|risk(?:ing|s)?|compromis\w*|sacrific\w*|disregard\w*|ignor\w*|neglect\w*|undermin\w*|regardless)\b", re.I)
flag = {}
for r in rows:
    for d, x in r["dilemmas"].items():
        flag[(r["id"], d)] = (bool(NEG.search(x["option_B"])), bool(NEG.search(x["option_A"])))
print("role option has evaluative clause:", np.mean([f[0] for f in flag.values()]).round(3),
      "| norm option has one:", np.mean([f[1] for f in flag.values()]).round(3))
prompts = {p["id"]: p for p in map(json.loads, open(ROOT / "data/e1_prompts.jsonl"))}
for f in sorted((ROOT / "runs/e1").glob("*.jsonl")):
    acc = collections.defaultdict(list)
    for g in map(json.loads, open(f)):
        p = prompts[g["id"]]
        a, b = math.exp(g["lpA"]), math.exp(g["lpB"])
        pa = a / (a + b) if a + b > 0 else 0.5
        pr = pa if p["role_letter"] == "A" else 1 - pa
        acc[(p["cond"], flag[(p["pid"], p["diff"])][0])].append(pr)
    print(f.stem, {f"{c}/{'neg' if k else 'clean'}": round(float(np.mean(v)), 3) for (c, k), v in sorted(acc.items())},
          "n_clean_items", len(acc[("value", False)]) // 4)
