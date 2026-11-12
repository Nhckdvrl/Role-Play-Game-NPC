"""S1 v3: prompt interventions on the v2 scenes (cost arrangements and option orders kept).

interventions (inserted right before the decision question):
  plain   : no intervention (replicates v2)
  consult : generic instruction to consider the role's own past experiences and feelings (no content)
  access  : generic reminder that the role knows only their own memories and attitudes
  bridge  : the K question about the role's attitude followed by its correct answer
            ("Does Maren trust the merchant Oswin? Yes.") - the inferred attitude made explicit next to the decision;
            in none/world/other conditions the correct answer is "No" for trust-type questions only when... (see below)
For bridge, the inserted answer is what the role actually holds: from its own stated attitude or experience;
for none / other / world conditions the role holds no attitude, so bridge inserts
"{role} has no particular feelings about this from personal experience." instead.

conditions: valence pos/neg (+ none), owner self/other/world, form stated/exp (world: exp only)
modes: P and EU, wording 0 and 1.

usage: python build_s3.py OUT.jsonl
"""
import json
import sys

from build_s2 import conditions, render, sheet
from families import FAMILIES

INTERVENTIONS = ("plain", "consult", "access", "bridge")


def insert_line(fam, iv, v, o):
    role = fam["role"]
    if iv == "plain":
        return ""
    if iv == "consult":
        return f"Before deciding, think about what {role} has personally experienced in the past and how {role} feels about the people and situations involved."
    if iv == "access":
        return f"Remember that {role} knows only {role}'s own memories and attitudes; other people's memories and events {role} has never heard of are unknown to {role}."
    if iv == "bridge":
        if o == "self" and v in ("pos", "neg"):
            ans = "Yes" if v == "pos" else "No"
            return f"{fam['kq'].format(role=role)} {ans}."
        return f"{role} has no particular feelings about this from personal experience."
    raise ValueError(iv)


def main(out):
    n = 0
    with open(out, "w") as fo:
        for fi, fam in enumerate(FAMILIES):
            for (v, o, f) in conditions():
                sh = sheet(fam, fi, v, o, f)
                for iv in INTERVENTIONS:
                    line = insert_line(fam, iv, v, o)
                    for mode in ("P", "EU"):
                        for conv in ("pos_costly", "neg_costly"):
                            for para in (0, 1):
                                for pos_first in (True, False):
                                    msgs = render(fam, mode, para, sh, pos_first, conv)
                                    if line:
                                        c = msgs[-1]["content"]
                                        q = c.rfind("\nA. ")
                                        qstart = c.rfind("\n\n", 0, q)  # start of the question line
                                        msgs[-1]["content"] = c[:qstart] + "\n\n" + line + c[qstart:]
                                    rid = f"{fam['id']}|{v}|{o}|{f}|{conv}|{mode}|{para}|{int(pos_first)}|{iv}"
                                    fo.write(json.dumps(dict(id=rid, family=fam["id"], kind=fam["kind"], valence=v, owner=o, form=f,
                                                             conv=conv, mode=mode, para=para, iv=iv,
                                                             pos_letter="A" if pos_first else "B", messages=msgs)) + "\n")
                                    n += 1
    print("wrote", n, "prompts to", out)


if __name__ == "__main__":
    main(sys.argv[1])
