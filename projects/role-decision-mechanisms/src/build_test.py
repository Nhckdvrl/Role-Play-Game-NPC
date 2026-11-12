"""Build the HELD-OUT test set (T set) from families_test.py in three context formats.

formats : card (dev-like character cards) | json (structured state) | prose (narrative background)
owners  : none; self (stated, exp); other (stated, exp); told (exp); world (exp)
modes   : K, P, EU (wording 0/1); decisions have both cost arrangements; option orders 2.
The decision/K question templates are the dev templates (frozen); only content, setting and format are new.

usage: python build_test.py OUT.jsonl
"""
import json
import random
import sys

from build_s2 import world_text
from families_test import TFAMILIES, TFILLER_ATT, TFILLER_EVENT, TFILLERS

FAR = {"city": "a city on the other side of the country", "station": "a mining station in another star system", "campus": "a university on another continent"}


def content(fam, fi, v, o, f):
    """Return role/other attitudes and memories, world event, as plain sentences (before formatting)."""
    rng = random.Random(5000 + fi)
    role, other = fam["role"], fam["other"]
    fills = rng.sample(TFILLERS[fam["setting"]], 6)
    atts = rng.sample(TFILLER_ATT, 2)
    slot = rng.randrange(3)
    mem = {role: [x.format(who=role) for x in fills[:3]], other: [x.format(who=other) for x in fills[3:]]}
    att = {role: atts[0].format(who=role), other: atts[1].format(who=other)}
    event = TFILLER_EVENT[fam["setting"]]
    met = False
    if v != "none":
        if o == "world":
            event = world_text(fam[f"exp_{v}"])
        elif o == "told":
            mem[other][slot] = fam[f"exp_{v}"].format(who=other)
            mem[role][slot] = f"{other}, whom {role} met once at a conference, told {role} this story about {other}'s own past: \"{fam[f'exp_{v}'].format(who=other)}\""
            met = True
        else:
            who = role if o == "self" else other
            if f == "stated":
                att[who] = fam[f"stated_{v}"].format(who=who)
            else:
                mem[who][slot] = fam[f"exp_{v}"].format(who=who)
    return att, mem, event, met


def render_context(fam, fi, v, o, f, fmt):
    att, mem, event, met = content(fam, fi, v, o, f)
    role, other = fam["role"], fam["other"]
    home = fam["home"]
    ohome = FAR[fam["setting"]] + (f"; {other} met {role} once at a conference" if met else f"; {other} has never met {role} and has never been to {home}")
    order = [role, other] if fi % 2 == 0 else [other, role]
    info = {role: (fam["occ"], home), other: ("traveller" if fam["setting"] != "station" else "freight pilot", ohome)}
    if fmt == "card":
        blocks = []
        for n in order:
            occ, h = info[n]
            ms = "\n".join(f"- {m}" for m in mem[n])
            blocks.append(f"Character: {n}\nOccupation: {occ}\nHome: {h}\nAttitudes: {att[n]}\nMemories:\n{ms}")
        return "Characters in this story:\n\n" + "\n\n".join(blocks) + f"\n\nEvents elsewhere (nobody in {home} has heard of them):\n- {event}"
    if fmt == "json":
        d = {"characters": [{"name": n, "occupation": info[n][0], "home": info[n][1], "attitudes": [att[n]], "memories": mem[n]} for n in order],
             "events_elsewhere_unknown_to_anyone_in_" + home.replace(" ", "_"): [event]}
        return "Game state:\n" + json.dumps(d, indent=1, ensure_ascii=False)
    if fmt == "prose":
        paras = []
        for n in order:
            occ, h = info[n]
            paras.append(f"{n} is {'an' if occ[0] in 'aeiou' else 'a'} {occ} ({h}). {att[n]} " + " ".join(mem[n]))
        return "Background.\n\n" + "\n\n".join(paras) + f"\n\nMeanwhile, far away and unknown to anyone in {home}: {event}"
    raise ValueError(fmt)


def question(fam, mode, para, ctx, pos_first, conv):
    role = fam["role"]
    pos_t, neg_t = ("Yes", "No") if mode == "K" else (fam["opt_pos"], fam["opt_neg"])
    opts = f"A. {pos_t}\nB. {neg_t}" if pos_first else f"A. {neg_t}\nB. {pos_t}"
    tail = ["Answer with the letter A or B only.", "Reply with A or B."][para]
    kq = fam["kq"].format(role=role)
    if mode == "K":
        body = [f"{ctx}\n\nQuestion: {kq}\n{opts}\n{tail}",
                f"Read the character information below and answer the question.\n\n{ctx}\n\n{kq}\n{opts}\n{tail}"][para]
        return [{"role": "user", "content": body}]
    scene = (fam["scene"] + " " + (fam["cost_pos"] if conv == "pos_costly" else fam["cost_neg"])).format(role=role)
    if mode == "P":
        body = [f"{ctx}\n\nSituation: {scene}\n\nWhat will {role} most likely do?\n{opts}\n{tail}",
                f"Read the character information and the situation below.\n\n{ctx}\n\n{scene}\n\nWhich option is {role} more likely to choose?\n{opts}\n{tail}"][para]
    else:
        body = [f"You are {role}. Stay in character.\n\n{ctx}\n\nSituation: {scene}\n\nWhat do you do?\n{opts}\n{tail}",
                f"Play the character {role}, using the information below, and decide as {role}.\n\n{ctx}\n\n{scene}\n\nWhich do you choose?\n{opts}\n{tail}"][para]
    return [{"role": "user", "content": body}]


def conds():
    yield ("none", "none", "none")
    for v in ("pos", "neg"):
        for o, f in (("self", "stated"), ("self", "exp"), ("other", "stated"), ("other", "exp"), ("told", "exp"), ("world", "exp")):
            yield (v, o, f)


def main(out):
    n = 0
    with open(out, "w") as fo:
        for fi, fam in enumerate(TFAMILIES):
            for fmt in ("card", "json", "prose"):
                for (v, o, f) in conds():
                    ctx = render_context(fam, fi, v, o, f, fmt)
                    for mode in ("K", "P", "EU"):
                        for conv in (("na",) if mode == "K" else ("pos_costly", "neg_costly")):
                            for para in (0, 1):
                                for pf in (True, False):
                                    rid = f"{fam['id']}|{v}|{o}|{f}|{conv}|{mode}|{para}|{int(pf)}|{fmt}"
                                    fo.write(json.dumps(dict(id=rid, family=fam["id"], setting=fam["setting"], kind=fam["kind"], fmt=fmt,
                                                             valence=v, owner=o, form=f, conv=conv, mode=mode, para=para,
                                                             pos_letter="A" if pf else "B", messages=question(fam, mode, para, ctx, pf, conv))) + "\n")
                                    n += 1
    print("wrote", n, "to", out)


if __name__ == "__main__":
    main(sys.argv[1])
