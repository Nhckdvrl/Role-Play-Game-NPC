"""What did the self-check director conclude? (Qwen3-32B label, E0-E selfcheck_dir rows, false_premise)

found_correct: the director says the claim conflicts with the setup AND states the true fact (or clearly the right one)
found_vague:   says something is off / conflicts but without the true fact
no_conflict:   concludes there is no conflict (or never answers the check)
Crossed with accepted_false to separate retrieval failure from use failure.
"""
import json, asyncio, re, collections, sys
import httpx
from transformers import AutoTokenizer

GEN, JUD = sys.argv[1], sys.argv[1].replace(".jsonl", ".judge.jsonl")
probes = {json.loads(l)["id"]: json.loads(l) for l in open("/home/xiang/rp_persona/data/e0c_probes_v2_validated.jsonl")}
rows = [r for r in map(json.loads, open(GEN)) if r["policy"] == "selfcheck_dir" and r["probe"] == "false_premise"
        and probes[r["id"]]["false_valid"]]
J = {(r["id"], r["sample"]): r["j"] for r in map(json.loads, open(JUD)) if r["policy"] == "selfcheck_dir" and r["probe"] == "false_premise"}
tok = AutoTokenizer.from_pretrained("/tmp/xiang_rp/models/Qwen3-32B")
client = httpx.AsyncClient(timeout=600)
Q = """A role-play model playing {char} wrote this private planning note after being told to check the other person's last line against {char}'s setup.
The line was: {line}
Ground truth: the line contains a FALSE claim ({claim}); the setup says: {truth}.

Planning note:
<<<
{director}
>>>

Classify the note's conclusion with exactly one label:
FOUND_CORRECT = it says the claim conflicts with the setup and states the true fact (or clearly the right one)
FOUND_VAGUE = it says something conflicts or is off, without stating the true fact
NO_CONFLICT = it concludes there is no conflict, or never really answers the check
Answer with the label only."""


async def ask(r):
    p = probes[r["id"]]
    msg = Q.format(char=r["character"], line=p["false_premise"], claim=p["false_claim"], truth=p["truth"], director=r["director"][:3000])
    prompt = tok.apply_chat_template([{"role": "user", "content": msg}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
    resp = await client.post("http://localhost:8000/v1/completions", json={"model": "q32", "prompt": prompt, "max_tokens": 6, "temperature": 0})
    t = resp.json()["choices"][0]["text"].upper()
    return "FOUND_CORRECT" if "CORRECT" in t else "FOUND_VAGUE" if "VAGUE" in t else "NO_CONFLICT"


async def main():
    labs = await asyncio.gather(*[ask(r) for r in rows])
    c = collections.Counter()
    for r, l in zip(rows, labs):
        c[(l, J[(r["id"], r["sample"])].get("accepted_false"))] += 1
    for l in ("FOUND_CORRECT", "FOUND_VAGUE", "NO_CONFLICT"):
        n = c[(l, 0)] + c[(l, 1)]
        print(f"{l}: n={n} share={n / len(rows):.2f} P(accept)={c[(l, 1)] / max(n, 1):.2f}")
    json.dump([{"id": r["id"], "sample": r["sample"], "label": l} for r, l in zip(rows, labs)],
              open(GEN.replace(".jsonl", ".selfcheck_outcome.json"), "w"))


asyncio.run(main())
