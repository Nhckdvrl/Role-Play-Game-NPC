"""Per-character lexical amplification: how often do a character's most distinctive
original words appear in generated vs original test lines (Friends)."""
import collections, json, math, re, sys
from pathlib import Path
ROOT = Path.home() / "rp_voice"
slots = {s["slot"]: s for s in map(json.loads, open(ROOT / "data/slots/slots.jsonl"))}
train = json.load(open(ROOT / "data/slots/train_lines.json"))["friends"]
gens = collections.defaultdict(dict)
for f in (ROOT / "runs").glob("*.jsonl"):
    for r in map(json.loads, open(f)):
        gens[f"{r['model']}:{r['cond']}"][r["slot"]] = r["text"]
tok = lambda t: re.findall(r"[a-z']+", t.lower())
cnt = {c: collections.Counter(w for t in L for w in tok(t)) for c, L in train.items()}
tot = collections.Counter(); [tot.update(v) for v in cnt.values()]
N = sum(tot.values())
top = {}
for c, v in cnt.items():
    n = sum(v.values())
    score = {w: math.log((v[w] + 1) / (n + 1)) - math.log((tot[w] - v[w] + 1) / (N - n + 1)) for w in v if v[w] >= 30}
    top[c] = sorted(score, key=score.get, reverse=True)[:15]
print({c.split()[0]: top[c][:8] for c in top})
srcs = ["original"] + sorted(gens)
print("rate of own top-15 distinctive words per 100 tokens")
for c in train:
    sids = [s for s, x in slots.items() if x["character"] == c]
    row = []
    for src in srcs:
        toks = [w for s in sids for w in tok(slots[s]["original"] if src == "original" else gens[src].get(s, ""))]
        row.append(f"{src.split(':')[0][:12]}={100*sum(w in top[c] for w in toks)/max(1,len(toks)):.1f}")
    print(c.split()[0], " ".join(row))
for src in srcs:
    L = [len((slots[s]["original"] if src == "original" else gens[src].get(s, "")).split()) for s in slots]
    print(src, "median words", sorted(L)[len(L)//2])
for c in ["Joey Tribbiani", "Chandler Bing"]:
    sids = [s for s, x in slots.items() if x["character"] == c][:4]
    for s in sids:
        print(c.split()[0], "| ORIG:", slots[s]["original"][:90], "| GEMMA:", gens["gemma3_12b:named"].get(s, "")[:90])
