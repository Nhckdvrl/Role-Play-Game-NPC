"""Frozen dev methods on the T set (decisions only, P and EU, wording 0/1, both costs and orders).

stage 'pre'   : writes  bridge_correct.jsonl (K question + correct answer before the question; for roles holding no
                attitude: "<kq> Nothing in <role>'s own experience says either way.")
                and k3.jsonl (three-way K: Yes / No / Nothing ...) for self-bridging
stage 'post'  : after scoring k3.jsonl, writes selfbridge3_<tag>.jsonl with the model's own 3-way answer inserted.

usage: python build_test_methods.py pre OUT_DIR
       python build_test_methods.py post OUT_DIR K3_RUN.jsonl TAG
"""
import json, math, sys
from collections import defaultdict
from build_test import conds, question, render_context
from families_test import TFAMILIES


def nothing(role):
    return f"Nothing in {role}'s own experience says either way."


def insert(msgs, line):
    c = msgs[-1]["content"]; q = c.rfind("\nA. "); qs = c.rfind("\n\n", 0, q)
    msgs[-1]["content"] = c[:qs] + "\n\n" + line + c[qs:]
    return msgs


def main():
    stage, out = sys.argv[1], sys.argv[2]
    if stage == "pre":
        with open(f"{out}/bridge_correct.jsonl", "w") as fb, open(f"{out}/k3.jsonl", "w") as fk:
            for fi, fam in enumerate(TFAMILIES):
                role = fam["role"]; kq = fam["kq"].format(role=role)
                for fmt in ("card", "json", "prose"):
                    for (v, o, f) in conds():
                        ctx = render_context(fam, fi, v, o, f, fmt)
                        holds = o in ("self", "told") and v in ("pos", "neg")
                        line = f"{kq} {'Yes' if v == 'pos' else 'No'}." if holds else f"{kq} {nothing(role)}"
                        for mode in ("P", "EU"):
                            for conv in ("pos_costly", "neg_costly"):
                                for para in (0, 1):
                                    for pf in (True, False):
                                        rid = f"{fam['id']}|{v}|{o}|{f}|{conv}|{mode}|{para}|{int(pf)}|{fmt}"
                                        fb.write(json.dumps(dict(id=rid, iv="bridge_correct", messages=insert(question(fam, mode, para, ctx, pf, conv), line))) + "\n")
                        for para in (0, 1):
                            for yes_first in (True, False):
                                a, b = ("Yes", "No") if yes_first else ("No", "Yes")
                                opts = f"A. {a}\nB. {b}\nC. {nothing(role)}"
                                tail = ["Answer with the letter A, B or C only.", "Reply with A, B or C."][para]
                                body = [f"{ctx}\n\nQuestion: {kq}\n{opts}\n{tail}", f"Read the character information below and answer the question.\n\n{ctx}\n\n{kq}\n{opts}\n{tail}"][para]
                                fk.write(json.dumps(dict(id=f"{fam['id']}|{v}|{o}|{f}|{fmt}|{para}|{int(yes_first)}", yes_letter="A" if yes_first else "B",
                                                         messages=[{"role": "user", "content": body}])) + "\n")
        print("ok pre")
    else:
        k3run, tag = sys.argv[3], sys.argv[4]
        meta = {json.loads(l)["id"]: json.loads(l) for l in open(f"{out}/k3.jsonl")}
        acc = defaultdict(lambda: [0.0, 0.0, 0.0])
        for l in open(k3run):
            o = json.loads(l); m = meta[o["id"]]
            ps = [math.exp(o.get(f"lp{x}", -math.inf)) for x in "ABC"]; z = sum(ps) or 1.0; ps = [p / z for p in ps]
            yes, no = (ps[0], ps[1]) if m["yes_letter"] == "A" else (ps[1], ps[0])
            key = "|".join(o["id"].split("|")[:6]); a = acc[key]; a[0] += yes; a[1] += no; a[2] += ps[2]
        ans = {k: ["Yes", "No", "Nothing"][max(range(3), key=lambda i: v[i])] for k, v in acc.items()}
        with open(f"{out}/selfbridge3_{tag}.jsonl", "w") as fo:
            for fi, fam in enumerate(TFAMILIES):
                role = fam["role"]; kq = fam["kq"].format(role=role)
                for fmt in ("card", "json", "prose"):
                    for (v, o, f) in conds():
                        ctx = render_context(fam, fi, v, o, f, fmt)
                        for mode in ("P", "EU"):
                            for conv in ("pos_costly", "neg_costly"):
                                for para in (0, 1):
                                    a = ans[f"{fam['id']}|{v}|{o}|{f}|{fmt}|{para}"]
                                    line = f"{kq} {a}." if a != "Nothing" else f"{kq} {nothing(role)}"
                                    for pf in (True, False):
                                        rid = f"{fam['id']}|{v}|{o}|{f}|{conv}|{mode}|{para}|{int(pf)}|{fmt}"
                                        fo.write(json.dumps(dict(id=rid, iv="selfbridge3", k_answer=a, messages=insert(question(fam, mode, para, ctx, pf, conv), line))) + "\n")
        print("ok post", tag)


if __name__ == "__main__":
    main()
