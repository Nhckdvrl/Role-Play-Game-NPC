"""S7: does the retrieval KEY decide whose experience counts?

Insert a QUESTION WITHOUT ANSWER right before the decision question:
  plain     : nothing
  q_role    : the K question, keyed on role + target ("Does Maren trust the merchant Oswin?")
  q_target  : a matching question keyed on the target only ("Is the merchant Oswin trustworthy?")
  bridge_qa : the K question with the correct answer (reference, as S3/S4)
Hypothesis (retrieval keyed by the decision's cue): q_role raises use of the role's own experience without
raising leaks; q_target raises use of any evidence about the target, so leaks rise too.

usage: python build_s7.py OUT.jsonl
"""
import json
import sys

from build_s2 import render, sheet
from families import FAMILIES

TQ = {
    "T01_merchant": "Is the travelling merchant Oswin trustworthy?",
    "T02_healer": "Is the healer Ilse a good healer?",
    "T03_captain": "Is the guard captain Varo honest?",
    "T04_loan": "Is the farmer Pell reliable with money?",
    "T05_smith": "Does the blacksmith Dorn do good work?",
    "T06_secret": "Can the neighbour Tamsin keep a secret?",
    "T07_guide": "Is the guide Rook trustworthy?",
    "T08_innkeeper": "Can the innkeeper Bess be trusted with valuables?",
    "T09_scholar": "Is the scholar Aldric's advice good?",
    "T10_cousin": "Does cousin Mira help when asked?",
    "T11_captain_ship": "Is the ship captain Hale trustworthy?",
    "T12_apprentice": "Can the apprentice Finn be trusted to run a shop?",
    "P01_water": "Is it safe to be out on the Grey River?",
    "P02_heights": "Are high places safe?",
    "P03_dogs": "Are farm dogs safe to be around?",
    "P04_venture": "Are cargo ventures a good investment?",
    "P05_forest": "Is the Blackwood safe at night?",
    "P06_debt": "Is borrowing from a moneylender a good idea?",
    "P07_capital": "Is the capital a good place to live?",
    "P08_horses": "Are horses safe to ride?",
    "P09_mushrooms": "Are wild mushrooms from the forest safe to eat?",
    "P10_speech": "Does speaking before a crowd go well?",
    "P11_bees": "Are bees good to keep?",
    "P12_stranger": "Can strangers be trusted?",
}
IVS = ("plain", "q_role", "q_target", "bridge_qa")


def conds():
    yield ("none", "none", "none")
    for v in ("pos", "neg"):
        for f in ("stated", "exp"):
            yield (v, "self", f)
            yield (v, "other", f)
        yield (v, "world", "exp")


def main(out):
    n = 0
    with open(out, "w") as fo:
        for fi, fam in enumerate(FAMILIES):
            role = fam["role"]
            kq = fam["kq"].format(role=role)
            for (v, o, f) in conds():
                sh = sheet(fam, fi, v, o, f)
                for iv in IVS:
                    if iv == "plain":
                        line = ""
                    elif iv == "q_role":
                        line = kq
                    elif iv == "q_target":
                        line = TQ[fam["id"]]
                    else:
                        if o == "self" and v in ("pos", "neg"):
                            line = f"{kq} {'Yes' if v == 'pos' else 'No'}."
                        else:
                            line = f"{role} has no particular feelings about this from personal experience."
                    for mode in ("P", "EU"):
                        for conv in ("pos_costly", "neg_costly"):
                            for para in (0, 1):
                                for pf in (True, False):
                                    msgs = render(fam, mode, para, sh, pf, conv)
                                    if line:
                                        c = msgs[-1]["content"]
                                        q = c.rfind("\nA. ")
                                        qs = c.rfind("\n\n", 0, q)
                                        msgs[-1]["content"] = c[:qs] + "\n\n" + line + c[qs:]
                                    rid = f"{fam['id']}|{v}|{o}|{f}|{conv}|{mode}|{para}|{int(pf)}|{iv}"
                                    fo.write(json.dumps(dict(id=rid, family=fam["id"], kind=fam["kind"], valence=v, owner=o, form=f, conv=conv,
                                                             mode=mode, para=para, iv=iv, pos_letter="A" if pf else "B", messages=msgs)) + "\n")
                                    n += 1
    print("wrote", n, "to", out)


if __name__ == "__main__":
    main(sys.argv[1])
