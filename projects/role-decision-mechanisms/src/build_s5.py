"""S5: self-bridging. Insert the MODEL'S OWN answer to the Knowing question right before the decision.

For every v2 condition (incl. other / world, where the role holds no attitude), we look up the model's
K answer for the same (family, valence, owner, form, wording) in its v2 run (option orders averaged;
answer = Yes if P(Yes) > 0.5) and insert "<K question> <Yes/No>." before the decision question.
If K is accurate about both the attitude and who-knows-what, self-bridging should raise use of the role's
own experience AND remove leaks; where K itself leaks (Qwen, Llama), the leak should persist.

usage: python build_s5.py V2_RUN.jsonl TAG OUT.jsonl
"""
import json
import math
import sys
from collections import defaultdict

from build_s2 import conditions, render, sheet
from families import FAMILIES

run, tag, out = sys.argv[1:4]
meta = {}
for l in open("/home/xiang/rp_mech/s2/data/prompts.jsonl"):
    r = json.loads(l)
    if r["mode"] == "K":
        meta[r["id"]] = r
acc = defaultdict(list)
for l in open(run):
    o = json.loads(l)
    if o["id"] not in meta:
        continue
    m = meta[o["id"]]
    pa, pb = math.exp(o["lpA"]), math.exp(o["lpB"])
    acc[(m["family"], m["valence"], m["owner"], m["form"], m["para"])].append((pa if m["pos_letter"] == "A" else pb) / (pa + pb))
kans = {k: ("Yes" if sum(v) / len(v) > 0.5 else "No") for k, v in acc.items()}
n = 0
with open(out, "w") as fo:
    for fi, fam in enumerate(FAMILIES):
        for (v, o, f) in conditions():
            sh = sheet(fam, fi, v, o, f)
            for mode in ("P", "EU"):
                for conv in ("pos_costly", "neg_costly"):
                    for para in (0, 1):
                        ans = kans[(fam["id"], v, o, f, para)]
                        line = f"{fam['kq'].format(role=fam['role'])} {ans}."
                        for pf in (True, False):
                            msgs = render(fam, mode, para, sh, pf, conv)
                            c = msgs[-1]["content"]
                            q = c.rfind("\nA. ")
                            qs = c.rfind("\n\n", 0, q)
                            msgs[-1]["content"] = c[:qs] + "\n\n" + line + c[qs:]
                            rid = f"{fam['id']}|{v}|{o}|{f}|{conv}|{mode}|{para}|{int(pf)}|selfbridge"
                            fo.write(json.dumps(dict(id=rid, family=fam["id"], kind=fam["kind"], valence=v, owner=o, form=f, conv=conv,
                                                     mode=mode, para=para, iv="selfbridge", k_answer=ans,
                                                     pos_letter="A" if pf else "B", messages=msgs)) + "\n")
                            n += 1
print("wrote", n, "to", out)
