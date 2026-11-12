"""S4: why does the 'bridge' (attitude Q&A right before the decision) work so well?

Starting from self-owned conditions (stated / exp; pos / neg) and 'none' / 'world' controls of v2, we vary
WHAT is inserted and WHERE:
  plain        : nothing inserted (v2)
  bridge_qa    : "<K question> Yes/No."                    right before the decision question   (S3 bridge)
  bridge_stmt  : the stated attitude sentence             right before the decision question   (recency, no Q&A format)
  bridge_exp   : the experience sentence repeated         right before the decision question   (recency of raw experience)
  qa_in_sheet  : "<K question> Yes/No." placed as an extra memory line in the role's sheet     (format, no recency)
  wrong_qa     : the K question with the OPPOSITE answer  right before the question            (does it override the sheet?)
  irrelevant_qa: a K-style Q&A about an unrelated filler attitude, right before the question  (generic Q&A proximity)
Modes P and EU, both wordings, both cost arrangements, both option orders.

usage: python build_s4.py OUT.jsonl
"""
import json
import sys

from build_s2 import render, sheet
from families import FAMILIES

IVS = ("plain", "bridge_qa", "bridge_stmt", "bridge_exp", "qa_in_sheet", "wrong_qa", "irrelevant_qa")


def conds():
    yield ("none", "none", "none")
    for v in ("pos", "neg"):
        for f in ("stated", "exp"):
            yield (v, "self", f)
        yield (v, "world", "exp")


def build(fam, fi, v, o, f, iv, mode, para, pos_first, conv):
    role = fam["role"]
    kq = fam["kq"].format(role=role)
    sh = sheet(fam, fi, v, o, f)
    holds = o == "self" and v in ("pos", "neg")
    ans = ("Yes" if v == "pos" else "No") if holds else None
    line = ""
    if iv == "bridge_qa" and holds:
        line = f"{kq} {ans}."
    elif iv == "bridge_stmt" and holds:
        line = fam[f"stated_{v}"].format(who=role)
    elif iv == "bridge_exp" and holds:
        line = fam[f"exp_{v}"].format(who=role)
    elif iv == "wrong_qa" and holds:
        line = f"{kq} {'No' if ans == 'Yes' else 'Yes'}."
    elif iv == "irrelevant_qa":
        line = f"Does {role} like the colour green? Yes."
    elif iv == "qa_in_sheet" and holds:
        tag = f"- {role} would answer the question \"{kq}\" with: {ans}."
        mem_head = f"Character: {role}\n"
        i = sh.find(mem_head)
        j = sh.find("Memories:\n", i) + len("Memories:\n")
        sh = sh[:j] + tag + "\n" + sh[j:]
    msgs = render(fam, mode, para, sh, pos_first, conv)
    if line:
        c = msgs[-1]["content"]
        q = c.rfind("\nA. ")
        qs = c.rfind("\n\n", 0, q)
        msgs[-1]["content"] = c[:qs] + "\n\n" + line + c[qs:]
    return msgs


def main(out):
    n = 0
    with open(out, "w") as fo:
        for fi, fam in enumerate(FAMILIES):
            for (v, o, f) in conds():
                for iv in IVS:
                    for mode in ("P", "EU"):
                        for conv in ("pos_costly", "neg_costly"):
                            for para in (0, 1):
                                for pf in (True, False):
                                    rid = f"{fam['id']}|{v}|{o}|{f}|{conv}|{mode}|{para}|{int(pf)}|{iv}"
                                    fo.write(json.dumps(dict(id=rid, family=fam["id"], kind=fam["kind"], valence=v, owner=o, form=f, conv=conv,
                                                             mode=mode, para=para, iv=iv, pos_letter="A" if pf else "B",
                                                             messages=build(fam, fi, v, o, f, iv, mode, para, pf, conv))) + "\n")
                                    n += 1
    print("wrote", n, "to", out)


if __name__ == "__main__":
    main(sys.argv[1])
