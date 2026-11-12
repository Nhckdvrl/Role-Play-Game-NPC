"""External validity on natural text: LifeChoice (Xu et al. 2024/2025; character decisions from novels, expert-written
story summaries up to the decision point). Original prompt template (test_llms.py), duplicated "A." prefixes removed.
conditions: full (story summary as Memory) | nomem (no story: scenario, question, options only)
option orders: original and reversed (scores are averaged per option identity).
usage: build_lifechoice.py DATA.json OUT.jsonl"""
import json, re, sys

TEMPLATE = """Please play the role of {name} based on the Profile and make your life choice under the Scenario regarding Question. Return the option letter (A, B, C, or D) that your character should most appropriately choose in the current scenario. The Profile consists of Description and Memory, where Description is an overall description of the character, and Memory consists of specific events the character has experienced.

# Inputs:
1. Profile:
1.1. Description
{name}

1.2. Memory
{memory}

2. Scenario:
{scenario}

3. Question:
{question}

4. Options:
A. {o0}
B. {o1}
C. {o2}
D. {o3}

# Outputs:
Your choice(A, B, C, or D):"""

data = json.load(open(sys.argv[1]))
n = 0
with open(sys.argv[2], "w") as fo:
    for bi, book in enumerate(data):
        for ri, r in enumerate(book):
            q = r["Multiple Choice Question"]
            opts = [re.sub(r"^\s*[A-D]\s*[\.\)]\s*", "", o).strip() for o in q["Options"]]
            if len(opts) != 4 or q["Correct Answer"] not in "ABCD":
                continue
            gold = "ABCD".index(q["Correct Answer"])
            for cond in ("full", "nomem"):
                mem = r["input_text"] if cond == "full" else "(none)"
                for order in ("orig", "rev"):
                    perm = [0, 1, 2, 3] if order == "orig" else [3, 2, 1, 0]
                    o = [opts[p] for p in perm]
                    body = TEMPLATE.format(name=r["character_name"], memory=mem, scenario=q["Scenario"], question=q["Question"], o0=o[0], o1=o[1], o2=o[2], o3=o[3])
                    fo.write(json.dumps(dict(id=f"{bi}|{ri}|{cond}|{order}", item=f"{bi}|{ri}", cond=cond, order=order, perm=perm, gold=gold,
                                             messages=[{"role": "user", "content": body}])) + "\n")
                    n += 1
print("wrote", n)
