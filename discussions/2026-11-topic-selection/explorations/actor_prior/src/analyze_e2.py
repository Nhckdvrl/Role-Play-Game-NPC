"""E2 analysis: P(role option) under recognize / predict / enact framings, per model,
plus the item-level gap: enact choice among items the model recognizes correctly."""
import collections
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path.home() / "rp_prior"
prompts = {r["id"]: r for r in map(json.loads, open(ROOT / "data/e2_prompts.jsonl"))}


def main():
    for f in sorted((ROOT / "runs/e2").glob("*.jsonl")):
        cells = collections.defaultdict(list)
        for g in map(json.loads, open(f)):
            p = prompts[g["id"]]
            a = math.exp(g["lpA"]) if g["lpA"] > -1e9 else 0.0
            b = math.exp(g["lpB"]) if g["lpB"] > -1e9 else 0.0
            if a + b == 0:
                continue
            pa = a / (a + b)
            cells[(p["pid"], p["diff"], p["cond"])].append(pa if p["role_letter"] == "A" else 1 - pa)
        c = {k: np.mean(v) for k, v in cells.items() if len(v) == 2}
        mean = {fr: np.mean([v for k, v in c.items() if k[2] == fr]) for fr in ("recognize", "predict", "enact")}
        items = {(k[0], k[1]) for k in c}
        rec_ok = [i for i in items if c.get((*i, "recognize"), 0) > 0.5]
        enact_given_rec = np.mean([c[(*i, "enact")] > 0.5 for i in rec_ok if (*i, "enact") in c])
        pred_given_rec = np.mean([c[(*i, "predict")] > 0.5 for i in rec_ok if (*i, "predict") in c])
        print(f"{f.stem:16s} P(role): recognize {mean['recognize']:.3f}  predict {mean['predict']:.3f}  enact {mean['enact']:.3f}"
              f" | items recognized {len(rec_ok)}/{len(items)}; of those, predicted-role {pred_given_rec:.3f}, enacted-role {enact_given_rec:.3f}")
        by = {d: np.mean([v for k, v in c.items() if k[1] == d and k[2] == "enact"]) for d in ("easy", "mid", "hard")}
        print(" " * 17, "enact by difficulty", {k: round(v, 3) for k, v in by.items()})


if __name__ == "__main__":
    main()
