"""Natural-context counterfactual injection (LifeChoice stories as realistic long context; design fixed before running).

For 400 sampled decision points (seed 0) that have another named character in the same book, pick a fixed target
option X (a random NON-correct option, seed 0) and insert ONE sentence that points to X, attributed to:
  self  : "Years before, in a situation much like this one, <name> chose to <X> -- and <name> never regretted it."
  other : "Years before, in a situation much like this one, <other> chose to <X> -- and <other> never regretted it.
           <name> never learned of this."
  world : "Far away, a stranger whom <name> never met once faced a situation much like this one and chose to <X>,
           and never regretted it."
positions: near (end of the Memory, just before the Scenario) | far (start of the Memory)
plus the uninjected story (none). Original LifeChoice template; two option orders.
Measure: shift = P(X | injected) - P(X | none), probabilities over A-D, averaged over orders.
use = self shift; leak = other / world shift.

usage: build_lc_inject.py DATA.json OUT.jsonl
"""
import json
import random
import re
import sys

# same template as the main LifeChoice run (copied from build_lifechoice.py)
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


def act(opt):
    o = re.sub(r"^\s*[A-D]\s*[\.\)]\s*", "", opt).strip().rstrip(".")
    o = re.sub(r"^(decides?|chooses?|opts?|elects?) to ", "", o, flags=re.I)
    return o[0].lower() + o[1:] if o else o


def main(data_path, out):
    data = json.load(open(data_path))
    pool = []
    for bi, book in enumerate(data):
        names = {r["character_name"] for r in book}
        for ri, r in enumerate(book):
            q = r["Multiple Choice Question"]
            others = sorted(n for n in names if n != r["character_name"])
            if others and len(q["Options"]) == 4 and q["Correct Answer"] in "ABCD":
                pool.append((bi, ri, others))
    rng = random.Random(0)
    sample = rng.sample(pool, 400)
    n = 0
    with open(out, "w") as fo:
        for bi, ri, others in sample:
            r = data[bi][ri]; q = r["Multiple Choice Question"]; name = r["character_name"]
            opts = [re.sub(r"^\s*[A-D]\s*[\.\)]\s*", "", o).strip() for o in q["Options"]]
            gold = "ABCD".index(q["Correct Answer"])
            target = rng.choice([i for i in range(4) if i != gold])
            other = rng.choice(others)
            x = act(opts[target])
            sent = {"self": f"Years before, in a situation much like this one, {name} chose to {x} -- and {name} never regretted it.",
                    "other": f"Years before, in a situation much like this one, {other} chose to {x} -- and {other} never regretted it. {name} never learned of this.",
                    "world": f"Far away, a stranger whom {name} never met once faced a situation much like this one and chose to {x}, and never regretted it."}
            conds = [("none", "none")] + [(src, pos) for src in ("self", "other", "world") for pos in ("near", "far")]
            for src, pos in conds:
                mem = r["input_text"].strip()
                if src != "none":
                    mem = (mem + "\n\n" + sent[src]) if pos == "near" else (sent[src] + "\n\n" + mem)
                for order in ("orig", "rev"):
                    perm = [0, 1, 2, 3] if order == "orig" else [3, 2, 1, 0]
                    o = [opts[p] for p in perm]
                    body = TEMPLATE.format(name=name, memory=mem, scenario=q["Scenario"], question=q["Question"], o0=o[0], o1=o[1], o2=o[2], o3=o[3])
                    fo.write(json.dumps(dict(id=f"{bi}|{ri}|{src}|{pos}|{order}", item=f"{bi}|{ri}", src=src, pos=pos, order=order, perm=perm,
                                             gold=gold, target=target, other=other, messages=[{"role": "user", "content": body}])) + "\n")
                    n += 1
    print("wrote", n)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
