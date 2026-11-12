"""S11: legitimate vs illegitimate access to another character's experience.

owner levels:
  self      : the role's own experience (should count)
  other     : another character's experience, never shared with the role (should NOT count)
  told      : the same other-character experience, plus a line in the ROLE's memories saying that
              the other character once told the role about it (should count, roughly like self)
  world     : unnamed traveller's experience listed as an unknown world event (should NOT count)
EU and P, wording 0/1, both cost arrangements and orders. Used both for plain decisions and for access gating
(mech_gate.py), which must keep 'told' while removing 'other'/'world'.

usage: python build_s11.py OUT.jsonl
"""
import json
import sys

import build_s2
from build_s2 import render
from families import FAMILIES


def sheet_told(fam, fi, v):
    sh = build_s2.sheet(fam, fi, v, "other", "exp")
    role, other = fam["role"], fam["other"]
    line = f"- {other}, a traveller {role} met once at the autumn fair, told {role} the following story about {other}'s own past: \"{fam[f'exp_{v}'].format(who=other)}\""
    head = f"Character: {role}\n"
    i = sh.find(head)
    j = sh.find("Memories:\n", i) + len("Memories:\n")
    sh = sh[:j] + line + "\n" + sh[j:]
    # the other character's block says they never met the role: relax it for 'told'
    sh = sh.replace(f"{other} has never met {role} and has never been to Ashford", f"{other} met {role} once at the autumn fair")
    return sh


def main(out):
    n = 0
    with open(out, "w") as fo:
        for fi, fam in enumerate(FAMILIES):
            conds = [("none", "none")] + [(v, o) for v in ("pos", "neg") for o in ("self", "other", "told", "world")]
            for v, o in conds:
                if o == "told":
                    sh = sheet_told(fam, fi, v)
                else:
                    sh = build_s2.sheet(fam, fi, v, o if v != "none" else "none", "exp" if v != "none" else "none")
                for mode in ("P", "EU"):
                    for conv in ("pos_costly", "neg_costly"):
                        for para in (0, 1):
                            for pf in (True, False):
                                f = "exp" if v != "none" else "none"
                                rid = f"{fam['id']}|{v}|{o}|{f}|{conv}|{mode}|{para}|{int(pf)}"
                                fo.write(json.dumps(dict(id=rid, family=fam["id"], kind=fam["kind"], valence=v, owner=o, form=f, conv=conv,
                                                         mode=mode, para=para, pos_letter="A" if pf else "B",
                                                         messages=render(fam, mode, para, sh, pf, conv))) + "\n")
                                n += 1
    print("wrote", n, "to", out)


if __name__ == "__main__":
    main(sys.argv[1])
