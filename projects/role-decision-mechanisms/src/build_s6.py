"""S6: self-bridging with a three-way Knowing question.

Step 1 (mode k3): K question with options Yes / No / "nothing in <role>'s own experience says either way",
  for every v2 condition, both wordings, two orders of Yes/No (the 'nothing' option is always C).
Step 2 (mode bridge): after scoring step 1, insert the model's own 3-way answer before the decision question:
  Yes -> "<kq> Yes."   No -> "<kq> No."   Nothing -> "<kq> Nothing in <role>'s own experience says either way."

usage: python build_s6.py k3 OUT.jsonl
       python build_s6.py bridge K3_PROMPTS.jsonl K3_RUN.jsonl OUT.jsonl
"""
import json
import math
import sys
from collections import defaultdict

from build_s2 import conditions, render, sheet
from families import FAMILIES


def nothing(role):
    return f"Nothing in {role}'s own experience says either way."


def k3_prompts(out):
    n = 0
    with open(out, "w") as fo:
        for fi, fam in enumerate(FAMILIES):
            role = fam["role"]
            kq = fam["kq"].format(role=role)
            for (v, o, f) in conditions():
                sh = sheet(fam, fi, v, o, f)
                for para in (0, 1):
                    for yes_first in (True, False):
                        a, b = ("Yes", "No") if yes_first else ("No", "Yes")
                        opts = f"A. {a}\nB. {b}\nC. {nothing(role)}"
                        tail = ["Answer with the letter A, B or C only.", "Reply with A, B or C."][para]
                        body = [f"{sh}\n\nQuestion: {kq}\n{opts}\n{tail}",
                                f"Read the character information below and answer the question.\n\n{sh}\n\n{kq}\n{opts}\n{tail}"][para]
                        rid = f"{fam['id']}|{v}|{o}|{f}|na|K3|{para}|{int(yes_first)}"
                        fo.write(json.dumps(dict(id=rid, family=fam["id"], valence=v, owner=o, form=f, para=para,
                                                 yes_letter="A" if yes_first else "B",
                                                 messages=[{"role": "user", "content": body}])) + "\n")
                        n += 1
    print("wrote", n, "to", out)


def bridge_prompts(k3p, k3r, out):
    meta = {json.loads(l)["id"]: json.loads(l) for l in open(k3p)}
    acc = defaultdict(lambda: [0.0, 0.0, 0.0])
    cnt = defaultdict(int)
    for l in open(k3r):
        o = json.loads(l)
        m = meta[o["id"]]
        ps = [math.exp(o.get(f"lp{x}", -math.inf)) for x in "ABC"]
        z = sum(ps) or 1.0
        ps = [p / z for p in ps]
        yes, no = (ps[0], ps[1]) if m["yes_letter"] == "A" else (ps[1], ps[0])
        key = (m["family"], m["valence"], m["owner"], m["form"], m["para"])
        a = acc[key]
        a[0] += yes; a[1] += no; a[2] += ps[2]
        cnt[key] += 1
    ans = {k: ["Yes", "No", "Nothing"][max(range(3), key=lambda i: v[i])] for k, v in acc.items()}
    n = 0
    with open(out, "w") as fo:
        for fi, fam in enumerate(FAMILIES):
            role = fam["role"]
            kq = fam["kq"].format(role=role)
            for (v, o, f) in conditions():
                sh = sheet(fam, fi, v, o, f)
                for mode in ("P", "EU"):
                    for conv in ("pos_costly", "neg_costly"):
                        for para in (0, 1):
                            a = ans[(fam["id"], v, o, f, para)]
                            line = f"{kq} {a}." if a != "Nothing" else f"{kq} {nothing(role)}"
                            for pf in (True, False):
                                msgs = render(fam, mode, para, sh, pf, conv)
                                c = msgs[-1]["content"]
                                q = c.rfind("\nA. ")
                                qs = c.rfind("\n\n", 0, q)
                                msgs[-1]["content"] = c[:qs] + "\n\n" + line + c[qs:]
                                rid = f"{fam['id']}|{v}|{o}|{f}|{conv}|{mode}|{para}|{int(pf)}|selfbridge3"
                                fo.write(json.dumps(dict(id=rid, family=fam["id"], kind=fam["kind"], valence=v, owner=o, form=f, conv=conv,
                                                         mode=mode, para=para, iv="selfbridge3", k_answer=a,
                                                         pos_letter="A" if pf else "B", messages=msgs)) + "\n")
                                n += 1
    print("wrote", n, "to", out)


if __name__ == "__main__":
    if sys.argv[1] == "k3":
        k3_prompts(sys.argv[2])
    else:
        bridge_prompts(*sys.argv[2:5])
