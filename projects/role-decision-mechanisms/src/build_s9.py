"""S9: event-style vs precedent-style experiences (slice-1 families, v2 scenes with cost counterbalance).

form: exp (event that happened to the owner, v2) | prec (a past choice of the same kind, no reason/outcome)
owner: self / other / world;  valence pos / neg (+ none);  modes K, P, EU;  wordings 2;  orders 2; costs 2 (decisions)
Hypothesis: decisions retrieve precedent ACTIONS by similarity regardless of owner -> prec >> exp in decisions,
and other/world precedents leak strongly; K should treat both forms more alike and exclude non-role owners.

usage: python build_s9.py OUT.jsonl
"""
import json
import random
import sys

import build_s2
from build_s2 import render, world_text
from families import FAMILIES
from families_prec import PREC


def sheet_prec(fam, fi, v, o):
    """Like build_s2.sheet but the episode is the precedent sentence."""
    f2 = dict(fam)
    pos, neg = PREC[fam["id"]]
    f2["exp_pos"], f2["exp_neg"] = pos, neg
    return build_s2.sheet(f2, fi, v, o, "exp")


def conds():
    yield ("none", "none", "none")
    for v in ("pos", "neg"):
        for o in ("self", "other", "world"):
            for f in ("exp", "prec"):
                yield (v, o, f)


def main(out):
    n = 0
    with open(out, "w") as fo:
        for fi, fam in enumerate(FAMILIES):
            for (v, o, f) in conds():
                sh = sheet_prec(fam, fi, v, o) if f == "prec" else build_s2.sheet(fam, fi, v, o, f)
                for mode in ("K", "P", "EU"):
                    for conv in (("na",) if mode == "K" else ("pos_costly", "neg_costly")):
                        for para in (0, 1):
                            for pf in (True, False):
                                rid = f"{fam['id']}|{v}|{o}|{f}|{conv}|{mode}|{para}|{int(pf)}"
                                fo.write(json.dumps(dict(id=rid, family=fam["id"], kind=fam["kind"], valence=v, owner=o, form=f, conv=conv,
                                                         mode=mode, para=para, pos_letter="A" if pf else "B",
                                                         messages=render(fam, mode, para, sh, pf, conv))) + "\n")
                                n += 1
    print("wrote", n, "to", out)


if __name__ == "__main__":
    main(sys.argv[1])
