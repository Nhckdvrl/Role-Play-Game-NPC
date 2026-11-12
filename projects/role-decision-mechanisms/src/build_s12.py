"""S12: is the 'profile region' penalty (S4) really dilution by other sheet content?

sheet variants for the role's stated attitude or experience (self, pos/neg; plus none):
  full     : v2 sheet (role card with 4 memories incl. 3 fillers, other character's card, world-events block)
  bare     : only the role's card with the single relevant line (no fillers, no other card, no world block)
placement: sheet (attitude/experience inside the card) | bridge (same sentence right before the question, card empty of it)
forms: stated / exp. Modes P, EU; both costs; wording 0/1; both orders.

usage: python build_s12.py OUT.jsonl
"""
import json
import sys

import build_s2
from build_s2 import render
from families import FAMILIES


def bare_sheet(fam, v, f, placement):
    role = fam["role"]
    att, mem = "", []
    if v != "none" and placement == "sheet":
        if f == "stated":
            att = fam[f"stated_{v}"].format(who=role)
        else:
            mem = [fam[f"exp_{v}"].format(who=role)]
    lines = [f"Character: {role}", f"Occupation: {fam['occ']}", "Home: the village of Ashford"]
    if att:
        lines.append(f"Attitudes: {att}")
    if mem:
        lines.append("Memories:\n" + "\n".join(f"- {m}" for m in mem))
    return "Characters in this story:\n\n" + "\n".join(lines)


def main(out):
    n = 0
    with open(out, "w") as fo:
        for fi, fam in enumerate(FAMILIES):
            conds = [("none", "none")] + [(v, f) for v in ("pos", "neg") for f in ("stated", "exp")]
            for v, f in conds:
                for sv in ("full", "bare"):
                    for pl in ("sheet", "bridge"):
                        if v == "none" and pl == "bridge":
                            continue
                        if sv == "full":
                            sh = build_s2.sheet(fam, fi, v if pl == "sheet" else "none", "self" if (v != "none" and pl == "sheet") else "none", f if pl == "sheet" else "none")
                        else:
                            sh = bare_sheet(fam, v, f, pl)
                        line = ""
                        if pl == "bridge" and v != "none":
                            line = fam[f"stated_{v}"].format(who=fam["role"]) if f == "stated" else fam[f"exp_{v}"].format(who=fam["role"])
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
                                        iv = f"{sv}_{pl}"
                                        rid = f"{fam['id']}|{v}|self|{f}|{conv}|{mode}|{para}|{int(pf)}|{iv}"
                                        fo.write(json.dumps(dict(id=rid, family=fam["id"], kind=fam["kind"], valence=v, owner="self" if v != "none" else "none",
                                                                 form=f, conv=conv, mode=mode, para=para, iv=iv, pos_letter="A" if pf else "B", messages=msgs)) + "\n")
                                        n += 1
    print("wrote", n, "to", out)


if __name__ == "__main__":
    main(sys.argv[1])
