"""Speaker distinguishability of original vs generated next lines.

fidelity: classifier trained on held-out ORIGINAL lines, tested on each source's lines
          (does the generated line sound like that character?).
separability: classifier trained and tested within one source by cross-validation
          (are that source's characters distinct from each other at all?).
Lines are aggregated into sets of k per character; sets are built from the same slots
for every source so comparisons are paired.
"""
import collections
import json
import random
import re
import sys
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

ROOT = Path.home() / "rp_voice"
slots = {s["slot"]: s for s in map(json.loads, open(ROOT / "data/slots/slots.jsonl"))}
train_lines = json.load(open(ROOT / "data/slots/train_lines.json"))
mask_names = json.load(open(ROOT / "data/slots/mask_names.json"))
gens = collections.defaultdict(dict)
for f in sorted((ROOT / "runs").glob("*.jsonl")):
    for r in map(json.loads, open(f)):
        gens[f"{r['model']}:{r['cond']}"][r["slot"]] = r["text"]
SOURCES = ["original"] + sorted(gens)


def masker(names):
    pats = [re.escape(n) for n in sorted(set(names), key=len, reverse=True) if len(n) > 1]
    rx = re.compile(r"\b(" + "|".join(pats) + r")\b", re.I) if pats else None
    return lambda t: rx.sub("NAME", t) if rx else t


def vec():
    return TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=2, sublinear_tf=True, max_features=200000)


def text_of(src, sid):
    return slots[sid]["original"] if src == "original" else gens[src].get(sid, "")


def make_sets(sids_by_char, k, seed):
    rng = random.Random(seed)
    sets = []
    for c, sids in sids_by_char.items():
        sids = sorted(sids)
        rng.shuffle(sids)
        sets += [(c, sids[i:i + k]) for i in range(0, len(sids) - k + 1, k)]
    return sets


def fidelity(group, k, seed=0):
    m = masker(mask_names[group])
    chars = list(train_lines[group])
    X = [m(t) for c in chars for t in train_lines[group][c]]
    y = [c for c in chars for _ in train_lines[group][c]]
    v = vec()
    clf = LogisticRegression(max_iter=3000, C=4).fit(v.fit_transform(X), y)
    by_char = collections.defaultdict(list)
    for sid, s in slots.items():
        if s["group"] == group:
            by_char[s["character"]].append(sid)
    sets = make_sets(by_char, k, seed)
    out = {}
    for src in SOURCES:
        docs = [m(" ".join(text_of(src, sid) for sid in ss)) for _, ss in sets]
        pred = clf.predict(v.transform(docs))
        out[src] = np.array([p == c for p, (c, _) in zip(pred, sets)], dtype=float)
    return out


def separability(group, k, folds=5, seed=0):
    m = masker(mask_names[group])
    by_char = collections.defaultdict(list)
    for sid, s in slots.items():
        if s["group"] == group:
            by_char[s["character"]].append(sid)
    sets = make_sets(by_char, k, seed)
    idx = np.arange(len(sets))
    np.random.default_rng(seed).shuffle(idx)
    out = {}
    for src in SOURCES:
        docs = [m(" ".join(text_of(src, sid) for sid in ss)) for _, ss in sets]
        lab = [c for c, _ in sets]
        hits = np.zeros(len(sets))
        for f in range(folds):
            te = idx[f::folds]
            tr = np.setdiff1d(idx, te)
            v = vec()
            clf = LogisticRegression(max_iter=3000, C=4).fit(v.fit_transform([docs[i] for i in tr]), [lab[i] for i in tr])
            hits[te] = clf.predict(v.transform([docs[i] for i in te])) == np.array([lab[i] for i in te])
        out[src] = hits
    return out


def ci(a, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    b = [rng.choice(a, len(a)).mean() for _ in range(n)]
    return a.mean(), np.percentile(b, 2.5), np.percentile(b, 97.5)


def report(name, per_group, chance):
    print(f"\n== {name} (chance {chance:.3f})")
    for src in SOURCES:
        a = np.concatenate([g[src] for g in per_group])
        mu, lo, hi = ci(a)
        print(f"  {src:28s} {mu:.3f} [{lo:.3f}, {hi:.3f}]  n={len(a)}")


def main():
    stats = {}
    for src in SOURCES:
        ts = [text_of(src, sid) for sid in slots]
        stats[src] = (np.median([len(t.split()) for t in ts]), np.mean([t == "" for t in ts]))
    print("median words / empty rate:", {s: (float(a), round(float(b), 3)) for s, (a, b) in stats.items()})
    cornell = sorted({s["group"] for s in slots.values() if s["corpus"] == "cornell"})
    for k in (1, 5, 10):
        report(f"Friends fidelity k={k}", [fidelity("friends", k)], 1 / 6)
        report(f"Friends separability k={k}", [separability("friends", k)], 1 / 6)
    for k in (1, 3, 5):
        report(f"Cornell fidelity k={k} ({len(cornell)} movies, 3-way)", [fidelity(g, k) for g in cornell], 1 / 3)
        report(f"Cornell separability k={k}", [separability(g, k, folds=3) for g in cornell], 1 / 3)


if __name__ == "__main__":
    main()
