"""Build S1 v2 prompts.

Changes from v1 (build_s1.py):
  * conv: which option carries an explicit cost (pos_costly / neg_costly), crossed with the attitude,
    so "role-consistent" and "convenient" are no longer the same option.
  * owner adds "world": the same episode happens to an unnamed traveller elsewhere in the kingdom and
    is listed as a world event that nobody in the role's village has heard of (experience form only).
    other-memory leak vs world-event leak separates misattribution from use of world evidence.
  * Every prompt has a world-events block (a neutral filler event when owner != world).
  * Block order alternates by family (v1 showed it barely matters); K is built once (it ignores the scene).

usage: python build_s2.py OUT.jsonl
"""
import json
import random
import re
import sys

from families import FAMILIES, FILLER_ATTITUDES, FILLER_MEMORIES
from families_v2 import V2

OTHER_OCC = ["tailor", "fisher", "mason", "brewer", "glassblower", "rope maker"]
FILLER_EVENTS = [
    "A new bell was cast for the great temple in the capital.",
    "The duke's eldest daughter was married in the spring.",
    "A comet was seen over the northern provinces for three nights.",
    "The old stone bridge at Kellen was finally repaired.",
]


def world_text(exp):
    """Turn an episode about {who} into one about an unnamed traveller."""
    first = [True]

    def rep(m):
        poss = m.group(0).endswith("'s")
        noun = "a traveller" if first[0] else "the traveller"
        first[0] = False
        return noun + ("'s" if poss else "")

    s = re.sub(r"\{who\}('s)?", rep, exp)
    return s[0].upper() + s[1:]


def block(name, occ, home, attitude, memories):
    mem = "\n".join(f"- {m}" for m in memories)
    return f"Character: {name}\nOccupation: {occ}\nHome: {home}\nAttitudes: {attitude}\nMemories:\n{mem}"


def sheet(fam, fi, valence, owner, form):
    rng = random.Random(1000 + fi)
    role, other = fam["role"], fam["other"]
    fills = rng.sample(FILLER_MEMORIES, 8)
    atts = rng.sample(FILLER_ATTITUDES, 2)
    slot = rng.randrange(4)
    event = FILLER_EVENTS[fi % len(FILLER_EVENTS)]
    mem = {role: [f.format(who=role) for f in fills[:4]], other: [f.format(who=other) for f in fills[4:]]}
    att = {role: atts[0].format(who=role), other: atts[1].format(who=other)}
    if valence != "none":
        if owner == "world":
            event = world_text(fam[f"exp_{valence}"])
        else:
            who = role if owner == "self" else other
            if form == "stated":
                att[who] = fam[f"stated_{valence}"].format(who=who)
            else:
                mem[who][slot] = fam[f"exp_{valence}"].format(who=who)
    occ_o = OTHER_OCC[sum(map(ord, fam["id"])) % len(OTHER_OCC)]
    b_role = block(role, fam["occ"], "the village of Ashford", att[role], mem[role])
    b_other = block(other, occ_o, f"a town on the far side of the kingdom; {other} has never met {role} and has never been to Ashford",
                    att[other], mem[other])
    parts = [b_role, b_other] if fi % 2 == 0 else [b_other, b_role]
    world = f"Events elsewhere in the kingdom (nobody in Ashford has heard of them):\n- {event}"
    return "Characters in this story:\n\n" + "\n\n".join(parts) + "\n\n" + world


def render(fam, mode, para, sh, pos_first, conv):
    role = fam["role"]
    v2 = V2[fam["id"]]
    if mode == "K":
        pos_t, neg_t = "Yes", "No"
        scene = ""
    else:
        pos_t, neg_t = v2["opt_pos"], v2["opt_neg"]
        cost = v2["cost_pos"] if conv == "pos_costly" else v2["cost_neg"]
        scene = (v2["scene"] + " " + cost).format(role=role)
    opts = f"A. {pos_t}\nB. {neg_t}" if pos_first else f"A. {neg_t}\nB. {pos_t}"
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
        yield (v, "world", "exp")


def main(out):
    n = 0
    with open(out, "w") as fo:
        for fi, fam in enumerate(FAMILIES):
            for (v, o, f) in conditions():
                sh = sheet(fam, fi, v, o, f)
                for mode in ("K", "P", "EU", "ES"):
                    for conv in (("na",) if mode == "K" else ("pos_costly", "neg_costly")):
                        for para in (0, 1):
                            for pos_first in (True, False):
                                rid = f"{fam['id']}|{v}|{o}|{f}|{conv}|{mode}|{para}|{int(pos_first)}"
                                fo.write(json.dumps(dict(
                                    id=rid, family=fam["id"], kind=fam["kind"], valence=v, owner=o, form=f,
                                    conv=conv, mode=mode, para=para, pos_letter="A" if pos_first else "B",
                                    messages=render(fam, mode, para, sh, pos_first, conv))) + "\n")
                                n += 1
    print("wrote", n, "prompts to", out)


if __name__ == "__main__":
    main(sys.argv[1])
