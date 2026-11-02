"""Build next-line slots for the voice feasibility test.

Each slot = (work, target character, preceding context, original line). Classifier
training lines come from disjoint material (Friends: seasons 1-7; Cornell: a
conversation-level 70/30 split inside each movie).
"""
import collections
import hashlib
import json
import random
import re
from pathlib import Path

ROOT = Path.home() / "rp_voice"
OUT = ROOT / "data" / "slots"
CTX_TURNS = 8
MIN_WORDS = 4
rng = random.Random(0)

FRIENDS_MAIN = ["Rachel Green", "Ross Geller", "Chandler Bing", "Monica Geller", "Joey Tribbiani", "Phoebe Buffay"]


def first_name(full):
    return full.split()[0]


def friends():
    utt = [json.loads(l) for l in open(ROOT / "data/friends-corpus/utterances.jsonl")]
    by_conv = collections.defaultdict(list)
    for u in utt:
        by_conv[u["conversation_id"]].append(u)
    train, slots = collections.defaultdict(list), collections.defaultdict(list)
    for cid, us in by_conv.items():
        us.sort(key=lambda u: u["id"])
        season = int(cid[1:3])
        for i, u in enumerate(us):
            if u["speaker"] not in FRIENDS_MAIN or len(u["text"].split()) < MIN_WORDS:
                continue
            if season <= 7:
                train[u["speaker"]].append(u["text"])
                continue
            ctx = []
            for p in us[max(0, i - CTX_TURNS):i]:
                if p["speaker"] == "TRANSCRIPT_NOTE":
                    ctx.append(f"[{p['text'].strip('()[] ')}]")
                else:
                    ctx.append(f"{first_name(p['speaker'])}: {p['text']}")
            if not ctx:
                continue
            slots[u["speaker"]].append({"context": ctx, "original": u["text"], "id": u["id"]})
    rows = []
    for s in FRIENDS_MAIN:
        for x in rng.sample(slots[s], 300):
            rows.append({"corpus": "friends", "work": "the TV sitcom Friends", "group": "friends",
                         "character": s, "name": first_name(s), **x})
    names = sorted({first_name(s) for s in FRIENDS_MAIN} | {"Mon", "Pheebs", "Rach", "Joe", "Chan"})
    return rows, {"friends": {s: train[s] for s in FRIENDS_MAIN}}, {"friends": names}


def cornell(n_movies=60, per_char=30):
    d = ROOT / "data/cornell"
    rd = lambda f: [l.split(" +++$+++ ") for l in open(d / f, encoding="latin-1").read().splitlines()]
    lines = {p[0]: p for p in rd("movie_lines.txt") if len(p) == 5}
    titles = {p[0]: (p[1], p[2]) for p in rd("movie_titles_metadata.txt")}
    convs = collections.defaultdict(list)
    for p in rd("movie_conversations.txt"):
        convs[p[2]].append(eval(p[3]))  # list literal of line ids from the corpus file
    cnt = collections.Counter((p[2], p[3]) for p in lines.values())
    movie_chars = collections.defaultdict(list)
    for (m, name), c in cnt.items():
        if c >= 50 and name:
            movie_chars[m].append((c, name))
    eligible = sorted(m for m, cs in movie_chars.items() if len(cs) >= 3)
    chosen = rng.sample(eligible, n_movies)
    rows, train, names = [], {}, {}
    for m in chosen:
        top = [n for _, n in sorted(movie_chars[m], reverse=True)[:3]]
        names[m] = sorted({w for p in lines.values() if p[2] == m for w in [p[3].title()] if w})
        tr, sl = collections.defaultdict(list), collections.defaultdict(list)
        for conv in convs[m]:
            is_test = int(hashlib.md5("".join(conv).encode()).hexdigest(), 16) % 10 < 3
            for i, lid in enumerate(conv):
                p = lines.get(lid)
                if not p or p[3] not in top or len(p[4].split()) < MIN_WORDS:
                    continue
                if not is_test:
                    tr[p[3]].append(p[4])
                elif i > 0:
                    ctx = [f"{lines[c][3].title()}: {lines[c][4]}" for c in conv[max(0, i - CTX_TURNS):i] if c in lines]
                    sl[p[3]].append({"context": ctx, "original": p[4], "id": lid})
        if min(len(sl[c]) for c in top) < 10 or min(len(tr[c]) for c in top) < 25:
            continue
        train[m] = {c: tr[c] for c in top}
        title, year = titles[m]
        for c in top:
            for x in rng.sample(sl[c], min(per_char, len(sl[c]))):
                rows.append({"corpus": "cornell", "work": f"the movie '{title.title()}' ({year})", "group": m,
                             "character": c, "name": c.title(), **x})
    return rows, train, names


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fr, frt, frn = friends()
    co, cot, con = cornell()
    with open(OUT / "slots.jsonl", "w") as f:
        for i, r in enumerate(fr + co):
            f.write(json.dumps({"slot": i, **r}, ensure_ascii=False) + "\n")
    json.dump({**frt, **cot}, open(OUT / "train_lines.json", "w"), ensure_ascii=False)
    json.dump({**frn, **con}, open(OUT / "mask_names.json", "w"), ensure_ascii=False)
    print("friends slots", len(fr), "cornell slots", len(co), "cornell movies", len(cot))
    print("median ctx turns", sorted(len(r["context"]) for r in fr + co)[len(fr + co) // 2])


if __name__ == "__main__":
    main()
