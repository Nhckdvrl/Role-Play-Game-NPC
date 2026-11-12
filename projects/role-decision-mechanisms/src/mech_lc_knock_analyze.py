"""Summarise mech_lc_knock: mean P(target) shift relative to the uninjected story, per source, for each knockout variant.
usage: mech_lc_knock_analyze.py KNOCK.jsonl"""
import json, sys
from collections import defaultdict
rows = [r for r in map(json.loads, open(sys.argv[1])) if "res" in r]
none = {r["item"]: r["res"]["base"] for r in rows if r["src"] == "none"}
print(sys.argv[1].split("/")[-1], "quarters", rows[0]["quarters"], "rows", len(rows))
for src in ("self", "other"):
    acc = defaultdict(list)
    for r in rows:
        if r["src"] != src or r["item"] not in none:
            continue
        for k, v in r["res"].items():
            acc[k].append(v - none[r["item"]])
    print(f"{src:5s} n={len(acc['base'])} " + "  ".join(f"{k}={sum(v) / len(v):+.3f}" for k, v in sorted(acc.items(), key=lambda kv: (kv[0] != 'base', kv[0]))))
