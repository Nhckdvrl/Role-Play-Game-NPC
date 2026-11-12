"""Side-effect check for the role-decision SFT: general multiple-choice knowledge (MMLU 1000 test items, ARC-Challenge
500 test items; fixed seed), zero-shot, letter log-prob argmax. usage: build_capab.py OUT.jsonl"""
import json, random, sys
from datasets import load_dataset
rng = random.Random(0)
rows = []
mm = load_dataset("cais/mmlu", "all", split="test")
for i in rng.sample(range(len(mm)), 1000):
    r = mm[i]; rows.append(("mmlu", r["subject"], r["question"], r["choices"], "ABCD"[r["answer"]]))
arc = load_dataset("allenai/ai2_arc", "ARC-Challenge", split="test")
arc = [r for r in arc if len(r["choices"]["text"]) == 4]
for r in rng.sample(arc, 500):
    lab = r["choices"]["label"]; key = r["answerKey"]
    rows.append(("arc", "arc", r["question"], r["choices"]["text"], "ABCD"[lab.index(key)]))
with open(sys.argv[1], "w") as fo:
    for n, (src, sub, q, ch, ans) in enumerate(rows):
        body = f"{q}\nA. {ch[0]}\nB. {ch[1]}\nC. {ch[2]}\nD. {ch[3]}\nAnswer with the letter A, B, C or D only."
        fo.write(json.dumps(dict(id=f"{src}|{n}", src=src, subject=sub, answer=ans, messages=[{"role": "user", "content": body}])) + "\n")
print("wrote", len(rows))
