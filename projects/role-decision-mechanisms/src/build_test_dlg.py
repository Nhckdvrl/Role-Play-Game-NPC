"""T-dlg: the held-out T families rendered as DIALOGUE / story history instead of character sheets.

Generality check (methods frozen, nothing tuned on this set): do the phenomena (under-use of the role's
experience, leak of inaccessible evidence) and the frozen gating method carry over when role information
lives in a conversation history, as in deployed role-play and agents?

formats
  chatlog : one user message holding a narrated story log with scene headers that state who is present,
            then the frozen question (K / P / EU, wordings 0/1).
  chat    : real multi-turn messages. The user is the narrator, the assistant plays the role. Each story
            block is one narrator turn, followed by an identical neutral out-of-character acknowledgement
            from the assistant. Final user turn = the frozen EU question, or K asked out of character.
            (P is not defined in this format.)
Content per condition is exactly build_test.content(): same memories, attitudes, event, told construction.

usage: python build_test_dlg.py OUT.jsonl
"""
import json
import sys

from build_test import FAR, conds, content
from families_test import TFAMILIES

ACK = "(OOC: got it, go on.)"


def blocks(fam, fi, v, o, f):
    """Ordered list of (header, lines) story blocks."""
    att, mem, event, met = content(fam, fi, v, o, f)
    role, other, home = fam["role"], fam["other"], fam["home"]
    far = FAR[fam["setting"]]
    rb = (f"[Scene: {home}, where {role} lives and works as {'an' if fam['occ'][0] in 'aeiou' else 'a'} {fam['occ']}. {role} is present.]",
          [att[role]] + mem[role])
    ob = (f"[Scene: {far}. {role} is not present; {other} " + ("met " + role + " once at a conference" if met else "has never met " + role) + ".]",
          [att[other]] + mem[other])
    ev = (f"[News from far away. Nobody in {home} has heard of it.]", [event])
    order = [rb, ob] if fi % 2 == 0 else [ob, rb]
    return order + [ev]


def final_q(fam, mode, para, pos_first, conv, in_chat):
    role = fam["role"]
    pos_t, neg_t = ("Yes", "No") if mode == "K" else (fam["opt_pos"], fam["opt_neg"])
    opts = f"A. {pos_t}\nB. {neg_t}" if pos_first else f"A. {neg_t}\nB. {pos_t}"
    tail = ["Answer with the letter A or B only.", "Reply with A or B."][para]
    kq = fam["kq"].format(role=role)
    if mode == "K":
        return [f"Question: {kq}\n{opts}\n{tail}" if not in_chat else f"(Out of character) Question about the story: {kq}\n{opts}\n{tail}",
                f"Answer the question about the story.\n\n{kq}\n{opts}\n{tail}" if not in_chat else f"(OOC) Quick question outside the story: {kq}\n{opts}\n{tail}"][para]
    scene = (fam["scene"] + " " + (fam["cost_pos"] if conv == "pos_costly" else fam["cost_neg"])).format(role=role)
    if mode == "P":
        return [f"Situation: {scene}\n\nWhat will {role} most likely do?\n{opts}\n{tail}",
                f"{scene}\n\nWhich option is {role} more likely to choose?\n{opts}\n{tail}"][para]
    return [f"Situation: {scene}\n\nWhat do you do?\n{opts}\n{tail}",
            f"{scene}\n\nWhich do you choose?\n{opts}\n{tail}"][para]


def messages(fam, fi, v, o, f, fmt, mode, para, pf, conv):
    role = fam["role"]
    bl = blocks(fam, fi, v, o, f)
    if fmt == "chatlog":
        log = "Story so far:\n\n" + "\n\n".join(h + "\n" + "\n".join(ls) for h, ls in bl)
        q = final_q(fam, mode, para, pf, conv, False)
        intro = {"K": ["", "Read the story log below.\n\n"], "P": ["", "Read the story log and the situation below.\n\n"],
                 "EU": [f"You are {role}. Stay in character.\n\n", f"Play the character {role}, using the story below, and decide as {role}.\n\n"]}[mode][para]
        return [{"role": "user", "content": f"{intro}{log}\n\n{q}"}]
    msgs = []
    for j, (h, ls) in enumerate(bl):
        pre = f"You are {role}. Stay in character; I am the narrator. Story so far:\n\n" if j == 0 else ""
        msgs += [{"role": "user", "content": pre + h + "\n" + "\n".join(ls)}, {"role": "assistant", "content": ACK}]
    msgs.append({"role": "user", "content": final_q(fam, mode, para, pf, conv, True)})
    return msgs


def main(out):
    n = 0
    with open(out, "w") as fo:
        for fi, fam in enumerate(TFAMILIES):
            for fmt in ("chatlog", "chat"):
                for (v, o, f) in conds():
                    for mode in (("K", "P", "EU") if fmt == "chatlog" else ("K", "EU")):
                        for conv in (("na",) if mode == "K" else ("pos_costly", "neg_costly")):
                            for para in (0, 1):
                                for pf in (True, False):
                                    rid = f"{fam['id']}|{v}|{o}|{f}|{conv}|{mode}|{para}|{int(pf)}|{fmt}"
                                    fo.write(json.dumps(dict(id=rid, family=fam["id"], setting=fam["setting"], kind=fam["kind"], fmt=fmt,
                                                             valence=v, owner=o, form=f, conv=conv, mode=mode, para=para,
                                                             pos_letter="A" if pf else "B",
                                                             messages=messages(fam, fi, v, o, f, fmt, mode, para, pf, conv))) + "\n")
                                    n += 1
    print("wrote", n, "to", out)


if __name__ == "__main__":
    main(sys.argv[1])
