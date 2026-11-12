"""T-conflict: the role's OWN experience and INACCESSIBLE evidence point in OPPOSITE directions (held-out T families).

The T set only has inaccessible evidence alone (no competing own evidence). Real role-play / ToM failures
(false belief, curse of knowledge) are conflicts: what the role experienced vs what the reader knows.
Conditions (valence = the role's own experience):
  self        : own experience only (reference)
  self+other  : own experience + the other character's opposite experience (other never met the role)
  self+world  : own experience + the opposite story as an unknown world event
  self+told   : own experience + the other's opposite story that the other TOLD the role (legitimately known;
                not an error to integrate it -- reference for how much legitimately known counter-evidence pulls)
Metric: sens = P(pos | own pos) - P(pos | own neg). If inaccessible evidence is ignored, sens(self+X) = sens(self).
Reuses build_test rendering, question templates and fillers unchanged; methods are frozen.

usage: python build_test_conflict.py OUT.jsonl
"""
import json
import random
import sys

import build_test as bt
from build_s2 import world_text
from families_test import TFAMILIES, TFILLER_ATT, TFILLER_EVENT, TFILLERS

FLIP = {"pos": "neg", "neg": "pos"}


def content_conflict(fam, fi, v, o, f):
    rng = random.Random(5000 + fi)
    role, other = fam["role"], fam["other"]
    fills = rng.sample(TFILLERS[fam["setting"]], 6)
    atts = rng.sample(TFILLER_ATT, 2)
    slot = rng.randrange(3)
    mem = {role: [x.format(who=role) for x in fills[:3]], other: [x.format(who=other) for x in fills[3:]]}
    att = {role: atts[0].format(who=role), other: atts[1].format(who=other)}
    event = TFILLER_EVENT[fam["setting"]]
    met = False
    if v != "none":
        mem[role][slot] = fam[f"exp_{v}"].format(who=role)
        w = FLIP[v]
        if o == "self+other":
            mem[other][slot] = fam[f"exp_{w}"].format(who=other)
        elif o == "self+world":
            event = world_text(fam[f"exp_{w}"])
        elif o == "self+told":
            mem[other][slot] = fam[f"exp_{w}"].format(who=other)
            mem[role][(slot + 1) % 3] = (f"{other}, whom {role} met once at a conference, told {role} this story about {other}'s own past: "
                                         f"\"{fam[f'exp_{w}'].format(who=other)}\"")
            met = True
    return att, mem, event, met


bt.content = content_conflict  # render_context looks up content() at call time


def main(out):
    n = 0
    conds = [("none", "none", "none")] + [(v, o, "exp") for v in ("pos", "neg") for o in ("self", "self+other", "self+world", "self+told")]
    with open(out, "w") as fo:
        for fi, fam in enumerate(TFAMILIES):
            for fmt in ("card", "json", "prose"):
                for (v, o, f) in conds:
                    ctx = bt.render_context(fam, fi, v, o, f, fmt)
                    for mode in ("K", "P", "EU"):
                        for conv in (("na",) if mode == "K" else ("pos_costly", "neg_costly")):
                            for para in (0, 1):
                                for pf in (True, False):
                                    rid = f"{fam['id']}|{v}|{o}|{f}|{conv}|{mode}|{para}|{int(pf)}|{fmt}"
                                    fo.write(json.dumps(dict(id=rid, family=fam["id"], setting=fam["setting"], kind=fam["kind"], fmt=fmt,
                                                             valence=v, owner=o, form=f, conv=conv, mode=mode, para=para,
                                                             pos_letter="A" if pf else "B",
                                                             messages=bt.question(fam, mode, para, ctx, pf, conv))) + "\n")
                                    n += 1
    print("wrote", n, "to", out)


if __name__ == "__main__":
    main(sys.argv[1])
