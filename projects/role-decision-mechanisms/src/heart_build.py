"""HEART-Bench external validity: does externalising the role's conclusion help memory -> decision,
and is profile information under-used when it sits in a profile block rather than next to the question?

Stage 'base' writes:
  prompts.jsonl  : MCQ prompts for C0 nomem, C1 mem_sheet, C3 profile_sheet, C4 profile_bridge (2 option rotations)
  gen.jsonl      : generation prompts for the self-bridge (memories + scenario -> 2-3 sentence conclusion)
Stage 'bridge' (after generation) writes prompts_bridge.jsonl : C2 mem_selfbridge.

Retrieval: BM25 over each memory's summary/context/triggers/tags against the scenario text; the prompt shows
only the raw episode (content_full, first 900 characters), never the dataset's psychological interpretation.

usage: python heart_build.py base OUT_DIR
       python heart_build.py bridge OUT_DIR GEN_OUT.jsonl
"""
import json
import math
import re
import sys
from collections import Counter

import pandas as pd

D = "/home/xiang/rp_mech/data_ext/heart/data"
K_MEM = 6
STOP = set("the a an and or of to in on at for with is are was were be been it this that you your i my me he she they them his her their as by from".split())


def toks(s):
    return [w for w in re.findall(r"[a-z]+", s.lower()) if w not in STOP and len(w) > 2]


def bm25_top(query, docs, k):
    N = len(docs)
    dt = [Counter(toks(d)) for d in docs]
    avg = sum(sum(c.values()) for c in dt) / N
    df = Counter(w for c in dt for w in c)
    q = toks(query)
    scores = []
    for i, c in enumerate(dt):
        L = sum(c.values())
        s = 0.0
        for w in q:
            if w in c:
                idf = math.log(1 + (N - df[w] + 0.5) / (df[w] + 0.5))
                s += idf * c[w] * 2.2 / (c[w] + 1.2 * (0.25 + 0.75 * L / avg))
        scores.append(s)
    return sorted(range(N), key=lambda i: -scores[i])[:k]


def scen_text(s):
    te = s["trigger_event"]
    parts = [s["description_for_agent"], s["context_text"]]
    if isinstance(te, dict):
        parts += [str(v) for v in te.values()]
    return "\n\n".join(parts)


def load():
    C = pd.read_parquet(f"{D}/characters.parquet")
    S = pd.read_parquet(f"{D}/scenarios.parquet")
    Q = pd.read_parquet(f"{D}/mcq.parquet")
    return {r["id"]: r for _, r in C.iterrows()}, {r["id"]: r for _, r in S.iterrows()}, Q


def profile_text(c):
    pats = "; ".join(list(c["core_patterns"]))
    return f"{c['description']} {c['self_value_logic']} Typical patterns: {pats}."


def mem_block(c, s):
    mems = list(c["episodic_memory_set"])
    docs = [" ".join(str(m.get(k, "")) for k in ("content_summary", "context", "triggers", "relevance_tags")) for m in mems]
    idx = bm25_top(scen_text(s), docs, K_MEM)
    out = []
    for i in idx:
        m = mems[i]
        txt = m["content_full"][:900].rsplit(" ", 1)[0] + ("..." if len(m["content_full"]) > 900 else "")
        out.append(f"- ({m['timeline']}) {txt}")
    return "\n".join(out)


def mcq_prompt(c, s, opts, rot, sheet_extra="", near_q=""):
    labels = "ABCD"
    o = opts[rot:] + opts[:rot]
    lines = "\n".join(f"{labels[i]}. {x['content']}" for i, x in enumerate(o))
    correct = labels[[x["is_correct"] for x in o].index(True)]
    who = f"You are a {c['occupation'].lower()}."
    head = who + (f"\n\n{sheet_extra}" if sheet_extra else "")
    ctx = f"Situation (you are {s['age']} years old):\n{scen_text(s)}"
    nq = f"\n\n{near_q}" if near_q else ""
    body = f"{head}\n\n{ctx}{nq}\n\nWhich of these responses is most like what you would do?\n{lines}\n\nAnswer with the letter A, B, C or D only."
    return [{"role": "user", "content": body}], correct


def main():
    stage, out = sys.argv[1], sys.argv[2]
    C, S, Q = load()
    if stage == "base":
        with open(f"{out}/prompts.jsonl", "w") as fp, open(f"{out}/gen.jsonl", "w") as fg:
            for _, q in Q.iterrows():
                c, s = C[q["character_id"]], S[q["scenario_id"]]
                opts = list(q["options"])
                mb = mem_block(c, s)
                prof = profile_text(c)
                for rot in (0, 2):
                    for cond, extra, nq in (("nomem", "", ""), ("mem_sheet", f"Some of your memories:\n{mb}", ""),
                                            ("profile_sheet", f"About you: {prof}", ""), ("profile_bridge", "", f"About you: {prof}")):
                        msgs, corr = mcq_prompt(c, s, opts, rot, extra, nq)
                        fp.write(json.dumps(dict(id=f"{q['question_id']}|{cond}|{rot}", qid=q["question_id"], cond=cond, rot=rot, correct=corr, messages=msgs)) + "\n")
                g = (f"Here are some memories of a person:\n{mb}\n\nThis person now faces the following situation:\n{scen_text(s)}\n\n"
                     f"Based only on these memories, in two or three sentences: how is this person likely to feel in this situation, and what will matter most to them? Write in the second person (\"You ...\").")
                fg.write(json.dumps(dict(id=q["question_id"], messages=[{"role": "user", "content": g}])) + "\n")
    else:
        gen = {json.loads(l)["id"]: json.loads(l)["text"] for l in open(sys.argv[3])}
        with open(f"{out}/prompts_bridge.jsonl", "w") as fp:
            for _, q in Q.iterrows():
                c, s = C[q["character_id"]], S[q["scenario_id"]]
                opts = list(q["options"])
                mb = mem_block(c, s)
                for rot in (0, 2):
                    msgs, corr = mcq_prompt(c, s, opts, rot, f"Some of your memories:\n{mb}", f"Thinking about your memories: {gen[q['question_id']].strip()}")
                    fp.write(json.dumps(dict(id=f"{q['question_id']}|mem_selfbridge|{rot}", qid=q["question_id"], cond="mem_selfbridge", rot=rot, correct=corr, messages=msgs)) + "\n")
    print("ok", stage)


if __name__ == "__main__":
    main()
