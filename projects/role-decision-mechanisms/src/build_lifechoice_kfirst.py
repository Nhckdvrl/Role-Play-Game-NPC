"""LifeChoice K-first (natural-text analogue of the self-bridge; designed once, not tuned).
stage 'pre' : self-description prompts -- the same Memory and Scenario, NO question and NO options:
              "In one or two sentences, describe what <name> cares about most and how <name> tends to act in
               situations like this, based only on the Memory."  (greedy, 80 tokens)
stage 'post': decision prompts (condition full, both orders) with the model's own self-description inserted as
              "1.3. What you know about yourself" right after the Memory section.
usage: build_lifechoice_kfirst.py pre DATA.json OUT.jsonl
       build_lifechoice_kfirst.py post PROMPTS.jsonl GEN.jsonl OUT.jsonl"""
import json, re, sys

if sys.argv[1] == "pre":
    data = json.load(open(sys.argv[2]))
    with open(sys.argv[3], "w") as fo:
        for bi, book in enumerate(data):
            for ri, r in enumerate(book):
                q = r["Multiple Choice Question"]; name = r["character_name"]
                body = (f"Below is the Memory of the character {name}: specific events {name} has experienced.\n\n# Memory\n{r['input_text']}\n\n"
                        f"# Scenario\n{q['Scenario']}\n\nIn one or two sentences, describe what {name} cares about most and how {name} tends to act "
                        f"in situations like this, based only on the Memory.")
                fo.write(json.dumps(dict(id=f"{bi}|{ri}", messages=[{"role": "user", "content": body}])) + "\n")
    print("ok pre")
else:
    gen = {json.loads(l)["id"]: json.loads(l)["text"].strip() for l in open(sys.argv[3])}
    n = 0
    with open(sys.argv[4], "w") as fo:
        for l in open(sys.argv[2]):
            r = json.loads(l)
            if r["cond"] != "full":
                continue
            g = re.sub(r"\s+", " ", gen.get(r["item"], ""))[:600]
            c = r["messages"][0]["content"]
            c = c.replace("\n\n2. Scenario:\n", f"\n\n1.3. What you know about yourself\n{g}\n\n2. Scenario:\n", 1)
            r["messages"] = [{"role": "user", "content": c}]; r["id"] = r["id"].replace("|full|", "|kfirst|"); r["cond"] = "kfirst"
            fo.write(json.dumps(r) + "\n"); n += 1
    print("ok post", n)
