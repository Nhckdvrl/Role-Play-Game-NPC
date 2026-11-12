"""SFT data from DEV families only (slice-1 v2 prompts incl. told; values slice). Decisions only (P, EU).

Targets:
  role holds the attitude (self stated/exp, told)       -> the attitude's pole letter
  role holds nothing (none, other stated/exp, world)    -> the base model's own preferred letter in the matching
                                                           'none' prompt (same family, cost, mode, wording, order)
so the training signal is only "follow what the role holds; ignore what the role cannot know", without imposing
any preference where the role has no basis.

usage: python build_sft.py TAG BASE_V2_RUN.jsonl BASE_S11_RUN.jsonl BASE_S8_RUN.jsonl OUT.jsonl
"""
import json
import math
import random
import sys

tag, v2run, s11run, s8run, out = sys.argv[1:6]


def load(prompts, run):
    meta = {json.loads(l)["id"]: json.loads(l) for l in open(prompts)}
    pref = {}
    for l in open(run):
        o = json.loads(l)
        if o["id"] in meta:
            pref[o["id"]] = "A" if o["lpA"] >= o["lpB"] else "B"
    return meta, pref


def none_id(rid, m):
    parts = rid.split("|")
    parts[1], parts[2], parts[3] = "none", "none", "none"
    return "|".join(parts)


rows = []
for prompts, run in (("/home/xiang/rp_mech/s2/data/prompts.jsonl", v2run), ("/home/xiang/rp_mech/s11/data/prompts.jsonl", s11run),
                     ("/home/xiang/rp_mech/s8/data/prompts.jsonl", s8run)):
    meta, pref = load(prompts, run)
    for rid, m in meta.items():
        if m["mode"] not in ("P", "EU") or m.get("iv", "plain") != "plain":
            continue
        if m["owner"] in ("self", "told") and m["valence"] in ("pos", "neg"):
            pos = m["pos_letter"]
            tgt = pos if m["valence"] == "pos" else ("B" if pos == "A" else "A")
        else:
            nid = none_id(rid, m)
            if nid not in pref:
                continue
            # the none prompt has the same option order only if pos_letter matches; ids encode order, so it does
            tgt = pref[nid]
        rows.append({"id": rid, "family": m["family"], "owner": m["owner"], "valence": m["valence"],
                     "messages": m["messages"] + [{"role": "assistant", "content": tgt}]})
random.Random(0).shuffle(rows)
with open(out, "w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")
from collections import Counter
print("wrote", len(rows), Counter(r["owner"] for r in rows))
