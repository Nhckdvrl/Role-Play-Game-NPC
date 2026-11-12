"""Measurement validity: free-form in-character replies on the T set (card format), classified into options.

stage 'gen'   : prompts asking for a short in-character reply WITHOUT showing options
                (EU framing, wording 0; conditions none, self stated/exp, other exp, world exp, told exp; both costs).
stage 'judge' : for one generation file, build judge prompts: situation + the two options (both orders) + the reply,
                answer A / B / C (C = neither or unclear). The judge never sees the character sheet.

usage: python build_freegen.py gen OUT.jsonl
       python build_freegen.py judge GEN_PROMPTS.jsonl GEN_OUT.jsonl OUT.jsonl
"""
import json
import sys

from build_test import render_context
from families_test import TFAMILIES

CONDS = [("none", "none", "none")] + [(v, o, f) for v in ("pos", "neg") for o, f in
                                      (("self", "stated"), ("self", "exp"), ("other", "exp"), ("world", "exp"), ("told", "exp"))]


def scene_of(fam, conv):
    return (fam["scene"] + " " + (fam["cost_pos"] if conv == "pos_costly" else fam["cost_neg"])).format(role=fam["role"])


def main():
    if sys.argv[1] == "gen":
        with open(sys.argv[2], "w") as fo:
            for fi, fam in enumerate(TFAMILIES):
                role = fam["role"]
                for (v, o, f) in CONDS:
                    ctx = render_context(fam, fi, v, o, f, "card")
                    for conv in ("pos_costly", "neg_costly"):
                        body = (f"You are {role}. Stay in character.\n\n{ctx}\n\nSituation: {scene_of(fam, conv)}\n\n"
                                f"What do you do? Reply in character in one or two sentences, making your decision clear.")
                        rid = f"{fam['id']}|{v}|{o}|{f}|{conv}"
                        fo.write(json.dumps(dict(id=rid, family=fam["id"], valence=v, owner=o, form=f, conv=conv,
                                                 messages=[{"role": "user", "content": body}])) + "\n")
        print("ok gen")
    else:
        gp, go, out = sys.argv[2:5]
        meta = {json.loads(l)["id"]: json.loads(l) for l in open(gp)}
        fams = {f["id"]: f for f in TFAMILIES}
        with open(out, "w") as fo:
            for l in open(go):
                g = json.loads(l)
                m = meta[g["id"]]
                fam = fams[m["family"]]
                for pos_first in (True, False):
                    a, b = (fam["opt_pos"], fam["opt_neg"]) if pos_first else (fam["opt_neg"], fam["opt_pos"])
                    body = (f"Situation faced by {fam['role']}: {scene_of(fam, m['conv'])}\n\n{fam['role']}'s reply:\n\"\"\"{g['text'].strip()[:700]}\"\"\"\n\n"
                            f"Which option did {fam['role']} choose in this reply?\nA. {a}\nB. {b}\nC. Neither, or the reply does not make the choice clear\n"
                            f"Answer with the letter A, B or C only.")
                    fo.write(json.dumps(dict(id=f"{g['id']}|{int(pos_first)}", gen_id=g["id"], pos_letter="A" if pos_first else "B",
                                             messages=[{"role": "user", "content": body}])) + "\n")
        print("ok judge")


if __name__ == "__main__":
    main()
