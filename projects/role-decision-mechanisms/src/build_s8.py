"""S8 (slice 2): value priorities -> decision, in the slice-1 format.

conditions : none; pos/neg x self/other x stated/exp; pos/neg x world (exp only)
modes      : K (does the role hold priority A over B?), P, EU
iv         : plain | bridge_stmt (the role's stated priority placed right before the decision question; self only)
wordings 2, option orders 2. No cost manipulation (value dilemmas carry their own stakes).

usage: python build_s8.py OUT.jsonl
"""
import json
import sys

from build_s2 import sheet
from families_values import VFAMILIES


def render(fam, mode, para, sh, pos_first, line=""):
    role = fam["role"]
    scene = fam["scene"].format(role=role)
    pos_t, neg_t = ("Yes", "No") if mode == "K" else (fam["opt_pos"], fam["opt_neg"])
    opts = f"A. {pos_t}\nB. {neg_t}" if pos_first else f"A. {neg_t}\nB. {pos_t}"
    tail = ["Answer with the letter A or B only.", "Reply with A or B."][para]
    kq = fam["kq"].format(role=role)
    ins = f"\n\n{line}" if line else ""
    if mode == "K":
        body = [f"{sh}\n\nQuestion: {kq}\n{opts}\n{tail}",
                f"Read the character information below and answer the question.\n\n{sh}\n\n{kq}\n{opts}\n{tail}"][para]
    elif mode == "P":
        body = [f"{sh}\n\nSituation: {scene}{ins}\n\nWhat will {role} most likely do?\n{opts}\n{tail}",
                f"Read the character information and the situation below.\n\n{sh}\n\n{scene}{ins}\n\nWhich option is {role} more likely to choose?\n{opts}\n{tail}"][para]
    else:
        body = [f"You are {role}. Stay in character.\n\n{sh}\n\nSituation: {scene}{ins}\n\nWhat do you do?\n{opts}\n{tail}",
                f"Play the character {role}, using the information below, and decide as {role}.\n\n{sh}\n\n{scene}{ins}\n\nWhich do you choose?\n{opts}\n{tail}"][para]
    return [{"role": "user", "content": body}]


def conds():
    yield ("none", "none", "none")
    for v in ("pos", "neg"):
        for o in ("self", "other"):
            for f in ("stated", "exp"):
                yield (v, o, f)
        yield (v, "world", "exp")


def main(out):
    n = 0
    with open(out, "w") as fo:
        for fi, fam in enumerate(VFAMILIES):
            for (v, o, f) in conds():
                sh = sheet(fam, fi, v, o, f)
                for mode in ("K", "P", "EU"):
                    for iv in (("plain",) if mode == "K" else ("plain", "bridge_stmt")):
                        line = fam[f"stated_{v}"].format(who=fam["role"]) if (iv == "bridge_stmt" and o == "self") else ""
                        for para in (0, 1):
                            for pf in (True, False):
                                rid = f"{fam['id']}|{v}|{o}|{f}|na|{mode}|{para}|{int(pf)}|{iv}"
                                fo.write(json.dumps(dict(id=rid, family=fam["id"], kind="value", valence=v, owner=o, form=f, conv="na",
                                                         mode=mode, para=para, iv=iv, pos_letter="A" if pf else "B",
                                                         messages=render(fam, mode, para, sh, pf, line))) + "\n")
                                n += 1
    print("wrote", n, "to", out)


if __name__ == "__main__":
    main(sys.argv[1])
