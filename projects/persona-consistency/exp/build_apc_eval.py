"""Build a small single-turn eval set from APC's 12-character relevance data.

Each item: one user query + a sampled profile (all gold-relevant statements for the
query + random same-character distractors up to PROFILE_SIZE). The profile is what
the policy sees and what APC scores against, so "active" = relevant statements in
the shown profile, "passive" = everything else in the shown profile.
"""
import json, random, collections, argparse

FULL_NAMES = {
    "Spartacus": "Spartacus", "Newton": "Isaac Newton", "Caesar": "Julius Caesar",
    "Alice": "Alice Carter", "Socrates": "Socrates", "Martin": "Martin Luther King Jr.",
    "Bob": "Bob", "Voldemort": "Lord Voldemort", "Cleopatra": "Cleopatra",
    "Hermione": "Hermione Granger", "Beethoven": "Ludwig van Beethoven", "Eve": "Eve",
}
ORIGINAL = {"Alice", "Bob", "Eve"}  # invented characters: little parametric knowledge

ap = argparse.ArgumentParser()
ap.add_argument("--rel", default="/home/xiang/rp_persona/data/apc/all.relevance.json")
ap.add_argument("--out", default="/home/xiang/rp_persona/data/apc_eval_v1.jsonl")
ap.add_argument("--per_char", type=int, default=12)
ap.add_argument("--profile_size", type=int, default=24)
ap.add_argument("--seed", type=int, default=0)
args = ap.parse_args()

rng = random.Random(args.seed)
rows = json.load(open(args.rel))
stmts = collections.defaultdict(set)
rel = collections.defaultdict(set)
for x in rows:
    stmts[x["character"]].add(x["statement"])
    if x["relevant"] == "yes":
        rel[(x["character"], x["query"])].add(x["statement"])

items = []
for char in sorted(stmts):
    queries = sorted(q for (c, q) in rel if c == char)
    rng.shuffle(queries)
    for q in queries[: args.per_char]:
        gold = sorted(rel[(char, q)])
        others = sorted(stmts[char] - set(gold))
        rng.shuffle(others)
        profile = gold + others[: max(0, args.profile_size - len(gold))]
        rng.shuffle(profile)
        items.append({
            "id": f"{char}-{len(items):04d}", "character": char, "name": FULL_NAMES[char],
            "original_character": char in ORIGINAL, "query": q,
            "profile": profile, "gold_relevant": gold,
        })

with open(args.out, "w") as f:
    for it in items:
        f.write(json.dumps(it, ensure_ascii=False) + "\n")
print(len(items), "items ->", args.out)
print(collections.Counter(len(i["gold_relevant"]) for i in items))
