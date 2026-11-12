"""Identity slice: occupation (category cue) vs own experience (individuating cue) -> K / P / EU decisions.

conditions (v = valence of the manipulated cue; for occ_vs_exp, v = valence of the OCCUPATION, experience opposite):
  none | self/occ | self/exp | self/stated | other/occ | other/exp | self/occ_vs_exp | self/occ_and_exp
formats: card | prose.  Question templates: build_test.question (frozen T templates).
split: IDEV / ITEST (field 'split').

usage: python build_identity.py OUT.jsonl
"""
import json
import random
import sys

from build_test import question
from families_identity import IDEV, IFILL_ATT, IFILL_MEM, ITEST

FLIP = {"pos": "neg", "neg": "pos"}
OTHER_OCC = "accounts clerk"


def art(w):
    return ("an " if w[0].lower() in "aeiou" else "a ") + w


def render(fam, fi, v, o, f, fmt):
    rng = random.Random(7000 + fi)
    role, other = fam["role"], fam["other"]
    fills = rng.sample(IFILL_MEM, 6)
    atts = rng.sample(IFILL_ATT, 2)
    slot = rng.randrange(3)
    mem = {role: [x.format(who=role) for x in fills[:3]], other: [x.format(who=other) for x in fills[3:]]}
    att = {role: atts[0].format(who=role), other: atts[1].format(who=other)}
    occ = {role: fam["occ_neutral"], other: OTHER_OCC}
    if v != "none":
        who = role if o == "self" else other
        if f in ("occ", "occ_vs_exp", "occ_and_exp"):
            occ[who] = fam[f"occ_{v}"]
        if f in ("exp", "occ_vs_exp", "occ_and_exp"):
            ev = FLIP[v] if f == "occ_vs_exp" else v
            mem[who][slot] = fam[f"exp_{ev}"].format(who=who)
        if f == "stated":
            att[who] = fam[f"stated_{v}"].format(who=who)
    home = {role: "the town of Brinmouth", other: f"a city abroad; {other} has never met {role} and has never been to Brinmouth"}
    order = [role, other] if fi % 2 == 0 else [other, role]
    if fmt == "card":
        bl = []
        for n in order:
            ms = "\n".join(f"- {m}" for m in mem[n])
            bl.append(f"Character: {n}\nOccupation: {occ[n]}\nHome: {home[n]}\nAttitudes: {att[n]}\nMemories:\n{ms}")
        return "Characters in this story:\n\n" + "\n\n".join(bl)
    paras = []
    for n in order:
        h = "lives in the town of Brinmouth" if n == role else f"lives in a city abroad and has never met {role}"
        paras.append(f"{n} is {art(occ[n])} who {h}. {att[n]} " + " ".join(mem[n]))
    return "Background.\n\n" + "\n\n".join(paras)


def conds():
    yield ("none", "none", "none")
    for v in ("pos", "neg"):
        for o, f in (("self", "occ"), ("self", "exp"), ("self", "stated"), ("other", "occ"), ("other", "exp"), ("self", "occ_vs_exp"), ("self", "occ_and_exp")):
            yield (v, o, f)


def main(out):
    n = 0
    with open(out, "w") as fo:
        for split, fams in (("dev", IDEV), ("test", ITEST)):
            for fi, fam in enumerate(fams):
                for fmt in ("card", "prose"):
                    for (v, o, f) in conds():
                        ctx = render(fam, fi, v, o, f, fmt)
                        for mode in ("K", "P", "EU"):
                            for conv in (("na",) if mode == "K" else ("pos_costly", "neg_costly")):
                                for para in (0, 1):
                                    for pf in (True, False):
                                        rid = f"{fam['id']}|{v}|{o}|{f}|{conv}|{mode}|{para}|{int(pf)}|{fmt}"
                                        fo.write(json.dumps(dict(id=rid, family=fam["id"], split=split, fmt=fmt, valence=v, owner=o, form=f,
                                                                 conv=conv, mode=mode, para=para, pos_letter="A" if pf else "B",
                                                                 messages=question(fam, mode, para, ctx, pf, conv))) + "\n")
                                        n += 1
    print("wrote", n, "to", out)


if __name__ == "__main__":
    main(sys.argv[1])
