"""S10: slice-1 v2 scenes WITHOUT any cost sentence (no competing practical factor), plus the two cost
arrangements for reference, for event (exp) and stated forms, owners self / other / world.

usage: python build_s10.py OUT.jsonl
"""
import json
import sys

import build_s2
from build_s2 import conditions, sheet
from families import FAMILIES
from families_v2 import V2

_orig = build_s2.render


def render(fam, mode, para, sh, pos_first, conv):
    if conv != "nocost":
        return _orig(fam, mode, para, sh, pos_first, conv)
    saved = V2[fam["id"]]
    V2[fam["id"]] = dict(saved, cost_pos="", cost_neg="")
    try:
        msgs = _orig(fam, mode, para, sh, pos_first, "pos_costly")
    finally:
        V2[fam["id"]] = saved
    for m in msgs:
        m["content"] = m["content"].replace(" \n", "\n")
    return msgs


def main(out):
    n = 0
    with open(out, "w") as fo:
        for fi, fam in enumerate(FAMILIES):
            for (v, o, f) in conditions():
                sh = sheet(fam, fi, v, o, f)
                for mode in ("P", "EU"):
                    for conv in ("nocost",):
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
