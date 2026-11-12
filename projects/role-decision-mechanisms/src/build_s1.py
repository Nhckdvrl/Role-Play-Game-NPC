"""Build slice-1 prompts: experience -> belief/preference -> decision.

Factors per family:
  valence  : neg / pos / none (none = no relevant attitude or memory anywhere)
  owner    : self (the role) / other (a character who has never met the role)
  form     : stated (attitude line) / exp (episode in memories only)
  mode     : K (does the role hold the attitude?), P (third-person prediction),
             EU (first person, everything in the user turn), ES (first person, sheet in system turn)
  para     : two wordings per mode
  order    : option order (pos-pole option as A or as B)
  blocks   : role block first / other block first
Every character block always has one attitude line and four memories, so the
relevant content only replaces a filler of the same kind.

usage: python build_s1.py OUT.jsonl
"""
import json
import random
import sys

from families import FAMILIES, FILLER_ATTITUDES, FILLER_MEMORIES

OTHER_OCC = ["tailor", "fisher", "mason", "brewer", "glassblower", "rope maker"]


def block(name, occ, home, attitude, memories):
    mem = "\n".join(f"- {m}" for m in memories)
    return f"Character: {name}\nOccupation: {occ}\nHome: {home}\nAttitudes: {attitude}\nMemories:\n{mem}"


def sheet(fam, valence, owner, form, blocks_first, rng_seed):
    rng = random.Random(rng_seed)
    role, other = fam["role"], fam["other"]
    fills = rng.sample(FILLER_MEMORIES, 8)
    atts = rng.sample(FILLER_ATTITUDES, 2)
    slot = rng.randrange(4)  # where a relevant memory goes
    mem = {role: [f.format(who=role) for f in fills[:4]], other: [f.format(who=other) for f in fills[4:]]}
    att = {role: atts[0].format(who=role), other: atts[1].format(who=other)}
    if valence != "none":
        who = role if owner == "self" else other
        if form == "stated":
            att[who] = fam[f"stated_{valence}"].format(who=who)
        else:
            mem[who][slot] = fam[f"exp_{valence}"].format(who=who)
    occ_o = OTHER_OCC[sum(map(ord, fam["id"])) % len(OTHER_OCC)]
    b_role = block(role, fam["occ"], "the village of Ashford", att[role], mem[role])
    b_other = block(other, occ_o, f"a town on the far side of the kingdom; {other} has never met {role} and has never been to Ashford",
                    att[other], mem[other])
    parts = [b_role, b_other] if blocks_first == "role" else [b_other, b_role]
    return "Characters in this story:\n\n" + "\n\n".join(parts)


def options(a_text, b_text):
    return f"A. {a_text}\nB. {b_text}"


def render(fam, mode, para, sh, pos_first):
    role = fam["role"]
    scene = fam["scene"].format(role=role)
    if mode == "K":
        pos_t, neg_t = "Yes", "No"
    else:
        pos_t, neg_t = fam["opt_pos"], fam["opt_neg"]
    opts = options(pos_t, neg_t) if pos_first else options(neg_t, pos_t)
    tail = ["Answer with the letter A or B only.", "Reply with A or B."][para]
    kq = fam["kq"].format(role=role)
    if mode == "K":
        body = [f"{sh}\n\nQuestion: {kq}\n{opts}\n{tail}",
                f"Read the character information below and answer the question.\n\n{sh}\n\n{kq}\n{opts}\n{tail}"][para]
        return [{"role": "user", "content": body}]
    if mode == "P":
        body = [f"{sh}\n\nSituation: {scene}\n\nWhat will {role} most likely do?\n{opts}\n{tail}",
                f"Read the character information and the situation below.\n\n{sh}\n\n{scene}\n\nWhich option is {role} more likely to choose?\n{opts}\n{tail}"][para]
        return [{"role": "user", "content": body}]
    if mode == "EU":
        body = [f"You are {role}. Stay in character.\n\n{sh}\n\nSituation: {scene}\n\nWhat do you do?\n{opts}\n{tail}",
                f"Play the character {role}, using the information below, and decide as {role}.\n\n{sh}\n\n{scene}\n\nWhich do you choose?\n{opts}\n{tail}"][para]
        return [{"role": "user", "content": body}]
    if mode == "ES":
        sysm = [f"You are {role}. Stay in character and make every decision as {role}.\n\n{sh}",
                f"Role-play as {role}. Everything below describes your world.\n\n{sh}"][para]
        user = [f"Situation: {scene}\n\nWhat do you do?\n{opts}\n{tail}",
                f"{scene}\n\nWhich do you choose?\n{opts}\n{tail}"][para]
        return [{"role": "system", "content": sysm}, {"role": "user", "content": user}]
    raise ValueError(mode)


def conditions():
    yield ("none", "none", "none")
    for v in ("neg", "pos"):
        for o in ("self", "other"):
            for f in ("stated", "exp"):
                yield (v, o, f)


def main(out):
    n = 0
    with open(out, "w") as fo:
        for fi, fam in enumerate(FAMILIES):
            for (v, o, f) in conditions():
                for bf in ("role", "other"):
                    # same filler draw for every condition of a family -> only the manipulated slot changes
                    sh = sheet(fam, v, o, f, bf, rng_seed=1000 + fi)
                    for mode in ("K", "P", "EU", "ES"):
                        for para in (0, 1):
                            for pos_first in (True, False):
                                rid = f"{fam['id']}|{v}|{o}|{f}|{bf}|{mode}|{para}|{int(pos_first)}"
                                fo.write(json.dumps(dict(
                                    id=rid, family=fam["id"], kind=fam["kind"], valence=v, owner=o, form=f,
                                    blocks=bf, mode=mode, para=para, pos_letter="A" if pos_first else "B",
                                    messages=render(fam, mode, para, sh, pos_first))) + "\n")
                                n += 1
    print("wrote", n, "prompts to", out)


if __name__ == "__main__":
    main(sys.argv[1])
