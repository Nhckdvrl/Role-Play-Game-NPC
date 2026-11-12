"""K counterpart of the natural-context injection (E3): same 400 stories, same injected sentences and positions.
Question (access K): "Does <name> know that someone once chose to <X> in a situation like this?"  A/B = Yes/No,
both orders. Expected for a role-bound K: Yes for self, No for other (never learned) and world (never met) and none.
usage: build_lc_inject_k.py INJECT_PROMPTS.jsonl OUT.jsonl"""
import json, re, sys
rows = [json.loads(l) for l in open(sys.argv[1])]
n = 0
with open(sys.argv[2], "w") as fo:
    for r in rows:
        if r["order"] != "orig":
            continue
        c = r["messages"][0]["content"]
        name = re.search(r"Please play the role of (.+?) based on the Profile", c).group(1)
        mem = c[c.index("1.2. Memory\n") + len("1.2. Memory\n"):c.index("\n\n2. Scenario:")]
        scen = c[c.index("2. Scenario:\n") + len("2. Scenario:\n"):c.index("\n\n3. Question:")]
        opts = re.findall(r"^[A-D]\. (.*)$", c[c.index("4. Options:"):], flags=re.M)
        x = opts[r["perm"].index(r["target"])].rstrip(".")
        x = re.sub(r"^(decides?|chooses?|opts?|elects?) to ", "", x, flags=re.I)
        x = x[0].lower() + x[1:]
        for yes_first in (True, False):
            a, b = ("Yes", "No") if yes_first else ("No", "Yes")
            body = (f"Below is the Memory of the character {name}: specific events {name} has experienced or knows about.\n\n# Memory\n{mem}\n\n"
                    f"# Scenario\n{scen}\n\nQuestion: Does {name} know that someone once chose to {x} in a situation like this?\nA. {a}\nB. {b}\n"
                    f"Answer with the letter A or B only.")
            fo.write(json.dumps(dict(id=f"{r['item']}|{r['src']}|{r['pos']}|{int(yes_first)}", item=r["item"], src=r["src"], pos=r["pos"],
                                     yes_letter="A" if yes_first else "B", messages=[{"role": "user", "content": body}])) + "\n")
            n += 1
print("wrote", n)
