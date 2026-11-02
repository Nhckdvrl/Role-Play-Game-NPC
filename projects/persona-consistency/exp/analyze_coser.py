"""CoSER GCA: per-dimension means and scene-paired differences vs base (bootstrap over scenes), on all 200 scenes and
on the scenes whose book does not appear in our HER training conversations; plus flaw-type counts per dimension."""
import json, random, statistics as S, collections, sys

R = "/home/xiang/rp_persona/runs"
ACTORS = sys.argv[1].split(",") if len(sys.argv) > 1 else ["q8", "q8r1", "r2p2", "r2pp"]
DIMS = ["Storyline Consistency", "Anthropomorphism", "Character Fidelity", "Storyline Quality"]
norm = lambda s: s.lower().replace(" ", "")[:15]
bk = lambda i: i.split("_Chapter")[0].split("_None")[0].replace("_", " ")
train_books = {norm(bk(json.loads(l)["id"])) for l in open(f"{R}/../data/her_mt_train_v1.jsonl")}
E = {a: {e["idx"]: e for e in json.load(open(f"{R}/coser/eval_{a}.json"))} for a in ACTORS}
rng = random.Random(0)


def boot(v):
    bs = sorted(S.mean(rng.choice(v) for _ in v) for _ in range(2000))
    return f"{S.mean(v):6.2f} [{bs[50]:6.2f},{bs[1950]:6.2f}]"


for subset, keep in [("all scenes", lambda e: True), ("books not in our training data", lambda e: norm(e["book"]) not in train_books)]:
    ids = [i for i in E[ACTORS[0]] if keep(E[ACTORS[0]][i]) and all(i in E[a] for a in ACTORS)]
    print(f"\n## {subset} (n={len(ids)})")
    for d in DIMS + ["avg"]:
        val = lambda a, i: S.mean(E[a][i]["scores"].values()) if d == "avg" else E[a][i]["scores"][d]
        line = f"{d:22s} " + " | ".join(f"{a}: {boot([val(a, i) for i in ids])}" for a in ACTORS)
        print(line)
        for a in ACTORS[1:]:
            print(f"{'':22s}   {a} - {ACTORS[0]}: {boot([val(a, i) - val(ACTORS[0], i) for i in ids])}")

print("\n## flaw types (count per scene, all scenes)")
for d in DIMS:
    types = collections.Counter()
    per = {a: collections.Counter() for a in ACTORS}
    for a in ACTORS:
        for e in E[a].values():
            for f in e["critique"][d].get("flaws", []):
                t = str(f.get("type", "?"))[:40]
                per[a][t] += 1
                types[t] += 1
    for t, _ in types.most_common(6):
        print(f"{d[:14]:14s} {t:40s} " + " ".join(f"{a}:{per[a][t] / len(E[a]):.2f}" for a in ACTORS))
