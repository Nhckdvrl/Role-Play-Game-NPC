"""Batched APC scoring (relevance + NLI DeBERTa, official 12character weights).

For every generation row and every statement in the item's shown profile, store
  g      = P(relevant | statement, query)
  c, e   = P(contradict), P(entailed) of the statement vs. a text stage
for stages: visible reply, director (<system_thinking>), role_thinking, native <think>.
Official per-statement score: g*e + (1-g)*(1-c)  (score.py).
Feeding thinking text to the NLI model is out of its training domain; treat stage
scores as a probe of "does this text state the fact", to be spot-checked.
"""
import json, argparse, os, sys, torch
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from transformers import AutoTokenizer, AutoModelForSequenceClassification

ap = argparse.ArgumentParser()
ap.add_argument("--gen", nargs="+", required=True)
ap.add_argument("--data", default="/home/xiang/rp_persona/data/apc_eval_v1.jsonl")
ap.add_argument("--out_suffix", default=".apc.jsonl")
ap.add_argument("--bs", type=int, default=128)
ap.add_argument("--max_words", type=int, default=250)
args = ap.parse_args()

REL = "KomeijiForce/deberta-v3-large-relevance-12character"
NLI = "KomeijiForce/deberta-v3-large-nli-12character"


def rel_prompt(c, s, q):
    return f'''Character: {c}

Persona Statement: {s}

User Utterance: {q}

Does this user utterance should be responded by including the information in the given persona statement? Only answer "yes" or "no" without any explanation.'''


def nli_prompt(c, s, q, r):
    return f'''Character: {c}

Persona Statement: {s}

User Utterance: {q}

Response: {r}

For this response, is the given persona entailed, neutral, or contradict to it in natural language inference? Only answer "entailed", "neutral" or "contradict" without any explanation.'''


def load(name):
    t = AutoTokenizer.from_pretrained(name)
    m = AutoModelForSequenceClassification.from_pretrained(name, torch_dtype=torch.bfloat16).cuda().eval()
    return t, m


@torch.no_grad()
def run(tm, texts, bs):
    t, m = tm
    out = []
    order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
    res = [None] * len(texts)
    for b in range(0, len(order), bs):
        idx = order[b:b + bs]
        enc = t([texts[i] for i in idx], padding=True, truncation=True, max_length=512, return_tensors="pt").to("cuda")
        p = m(**enc).logits.float().softmax(-1).cpu().tolist()
        for i, pi in zip(idx, p):
            res[i] = pi
    return res


def trunc(s, n):
    w = s.split()
    return " ".join(w[:n])


items = {json.loads(l)["id"]: json.loads(l) for l in open(args.data)}
rel_m, nli_m = load(REL), load(NLI)
STAGES = ["visible", "director", "role_thinking", "think"]

for gpath in args.gen:
    rows = [json.loads(l) for l in open(gpath)]
    # relevance: unique (item, statement)
    rel_keys = sorted({(r["id"], s) for r in rows for s in items[r["id"]]["profile"]})
    rel_p = run(rel_m, [rel_prompt(items[i]["character"], s, items[i]["query"]) for i, s in rel_keys], args.bs)
    G = {k: p[1] for k, p in zip(rel_keys, rel_p)}
    nli_keys, nli_txt = [], []
    for ri, r in enumerate(rows):
        it = items[r["id"]]
        for st in STAGES:
            txt = r.get(st) or ""
            if not txt.strip():
                continue
            for si, s in enumerate(it["profile"]):
                nli_keys.append((ri, st, si))
                nli_txt.append(nli_prompt(it["character"], s, it["query"], trunc(txt, args.max_words)))
    print(gpath, "rel", len(rel_keys), "nli", len(nli_txt), flush=True)
    nli_p = run(nli_m, nli_txt, args.bs)
    per = {}
    for (ri, st, si), p in zip(nli_keys, nli_p):
        per.setdefault(ri, {}).setdefault(st, {})[si] = (p[0], p[2])
    with open(gpath.replace(".jsonl", args.out_suffix), "w") as f:
        for ri, r in enumerate(rows):
            it = items[r["id"]]
            stmts = []
            for si, s in enumerate(it["profile"]):
                d = {"g": G[(r["id"], s)], "gold": s in it["gold_relevant"]}
                for st in STAGES:
                    if st in per.get(ri, {}):
                        d[st] = per[ri][st][si]
                stmts.append(d)
            f.write(json.dumps({"id": r["id"], "cond": r["cond"], "sample": r["sample"], "policy": r["policy"],
                                "stmts": stmts}) + "\n")
    print("done", gpath, flush=True)
