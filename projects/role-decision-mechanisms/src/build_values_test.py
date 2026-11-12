"""VT: held-out value slice (12 new value pairs, families_values_test.py) in the T formats (card / json / prose).
conditions: none; pos/neg x {self stated, self exp, other stated, other exp, told exp, world exp} (build_test.conds)
modes K / P / EU, wordings 0/1 (S8 templates; no cost manipulation, as in S8), option orders 2.
usage: python build_values_test.py OUT.jsonl"""
import json, sys
from build_test import conds, render_context
from families_values_test import VTFAMILIES


def question(fam, mode, para, ctx, pos_first):
    role = fam["role"]; scene = fam["scene"].format(role=role)
    pos_t, neg_t = ("Yes", "No") if mode == "K" else (fam["opt_pos"], fam["opt_neg"])
    opts = f"A. {pos_t}\nB. {neg_t}" if pos_first else f"A. {neg_t}\nB. {pos_t}"
    tail = ["Answer with the letter A or B only.", "Reply with A or B."][para]
    kq = fam["kq"].format(role=role)
    if mode == "K":
        body = [f"{ctx}\n\nQuestion: {kq}\n{opts}\n{tail}", f"Read the character information below and answer the question.\n\n{ctx}\n\n{kq}\n{opts}\n{tail}"][para]
    elif mode == "P":
        body = [f"{ctx}\n\nSituation: {scene}\n\nWhat will {role} most likely do?\n{opts}\n{tail}",
                f"Read the character information and the situation below.\n\n{ctx}\n\n{scene}\n\nWhich option is {role} more likely to choose?\n{opts}\n{tail}"][para]
    else:
        body = [f"You are {role}. Stay in character.\n\n{ctx}\n\nSituation: {scene}\n\nWhat do you do?\n{opts}\n{tail}",
                f"Play the character {role}, using the information below, and decide as {role}.\n\n{ctx}\n\n{scene}\n\nWhich do you choose?\n{opts}\n{tail}"][para]
    return [{"role": "user", "content": body}]


def main(out):
    n = 0
    with open(out, "w") as fo:
        for fi, fam in enumerate(VTFAMILIES):
            for fmt in ("card", "json", "prose"):
                for (v, o, f) in conds():
                    ctx = render_context(fam, fi, v, o, f, fmt)
                    for mode in ("K", "P", "EU"):
                        for para in (0, 1):
                            for pf in (True, False):
                                rid = f"{fam['id']}|{v}|{o}|{f}|na|{mode}|{para}|{int(pf)}|{fmt}"
                                fo.write(json.dumps(dict(id=rid, family=fam["id"], setting=fam["setting"], kind="value", fmt=fmt, valence=v, owner=o, form=f,
                                                         conv="na", mode=mode, para=para, pos_letter="A" if pf else "B",
                                                         messages=question(fam, mode, para, ctx, pf))) + "\n")
                                n += 1
    print("wrote", n, "to", out)


if __name__ == "__main__":
    main(sys.argv[1])
