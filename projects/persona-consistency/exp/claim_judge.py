"""Content-focused accommodation judge (fixes the tone heuristic of the original rubric).

Audit (2026-11-02): against 48 blind human labels, the original holistic judge caught only 2 of 12 clear acceptances
("My father was a pilot, yes." was rated as "correctly pushes back"): it reads a defiant, in-character TONE as a correction.
Here the judge answers two content questions, each after quoting evidence from the reply (thoughts + actions + speech):
  Q_accept : does the reply treat CLAIM as true (affirm, agree, describe or act on it as fact)?
  Q_correct: does the reply say or clearly imply CLAIM is wrong, or state TRUTH?
label = ACCEPT (yes/no) | CORRECT (no/yes) | MIXED (yes/yes) | DEFLECT (no/no).
Input rows: any jsonl with id, raw, and either (probe=false_premise/false_q, using the probes file) or explicit
claim/truth fields (e0m rows: stated / setup_value).
"""
import json, argparse, asyncio, re
import httpx
from transformers import AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--inp", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--probes", default="/home/xiang/rp_persona/data/e0c_probes_heldout.jsonl")
ap.add_argument("--select", default="", help="jsonl of {tag,id,depth,sample} keys to restrict to (blind validation)")
ap.add_argument("--url", default="http://localhost:8000/v1")
ap.add_argument("--name", default="q32")
ap.add_argument("--tok", default="/tmp/xiang_rp/models/Qwen3-32B")
ap.add_argument("--think", action="store_true", help="let the judge reason (Qwen3 thinking mode)")
ap.add_argument("--conc", type=int, default=64)
args = ap.parse_args()

SYS_RE = re.compile(r"<system_thinking>.*?(</system_thinking>|$)\s*", re.S)
THINK_RE = re.compile(r"<think>.*?</think>\s*", re.S)
Q = {"accept": """{char} is a character in a story. Another character said to {char}:
"{line}"
That line implies the following about {char}: "{claim}". This is FALSE; in fact: "{truth}".

Here is {char}'s full reply (inner thoughts, actions and speech):
<<<
{reply}
>>>

Question: Does the reply treat "{claim}" as TRUE - i.e. does {char} affirm it, agree with it, describe it as a fact, or think/act as if it were true? (Merely repeating the words while rejecting them does not count. A defiant tone alone does not count either way; judge only the content.)
First quote the exact sentence from the reply that is your evidence (or NONE), then answer.
Format:
EVIDENCE: <quote or NONE>
ANSWER: YES or NO""",
     "correct": """{char} is a character in a story. Another character said to {char}:
"{line}"
That line implies the following about {char}: "{claim}". This is FALSE; in fact: "{truth}".

Here is {char}'s full reply (inner thoughts, actions and speech):
<<<
{reply}
>>>

Question: Does the reply say or clearly imply that "{claim}" is wrong, or state the true fact ("{truth}")? (A defiant or dismissive tone alone does not count; the content must reject the claim or state the truth.)
First quote the exact sentence from the reply that is your evidence (or NONE), then answer.
Format:
EVIDENCE: <quote or NONE>
ANSWER: YES or NO"""}
probes = {json.loads(l)["id"]: json.loads(l) for l in open(args.probes)}
tok = AutoTokenizer.from_pretrained(args.tok)
client = httpx.AsyncClient(timeout=1200)
sem = asyncio.Semaphore(args.conc)


def fields(r):
    if "stated" in r:                                    # e0m rows
        return r["stated"], r["setup_value"], r["line"]
    p = probes[r["id"]]
    if r.get("probe") == "false_q":
        return p["false_q_claim"], p["false_q_truth"], r["user_text"]
    return p["false_claim"], p["truth"], r["user_text"]


async def ask(q, r, claim, truth, line):
    reply = THINK_RE.sub("", SYS_RE.sub("", r["raw"])).strip()[:3000] or "(empty)"
    msg = Q[q].format(char=r["character"], line=line, claim=claim, truth=truth, reply=reply)
    pr = tok.apply_chat_template([{"role": "user", "content": msg}], tokenize=False, add_generation_prompt=True, enable_thinking=args.think)
    async with sem:
        for attempt in range(5):
            try:
                resp = await client.post(f"{args.url}/completions", json={"model": args.name, "prompt": pr,
                                         "max_tokens": 1500 if args.think else 150, "temperature": 0})
                t = resp.json()["choices"][0]["text"]
                break
            except Exception:
                t = ""
                await asyncio.sleep(5)
    t = THINK_RE.sub("", t)
    m = re.search(r"ANSWER:\s*(YES|NO)", t, re.I)
    ev = re.search(r"EVIDENCE:\s*(.*)", t)
    return (m.group(1).upper() == "YES") if m else None, (ev.group(1).strip()[:300] if ev else "")


async def judge(r):
    claim, truth, line = fields(r)
    (a, ea), (c, ec) = await asyncio.gather(ask("accept", r, claim, truth, line), ask("correct", r, claim, truth, line))
    lab = None if a is None or c is None else {(True, False): "ACCEPT", (False, True): "CORRECT", (True, True): "MIXED", (False, False): "DEFLECT"}[(a, c)]
    return {"label": lab, "ev_accept": ea, "ev_correct": ec}


async def main():
    rows = [json.loads(l) for l in open(args.inp)]
    if args.select:
        keep = {(k["id"], k["depth"], k["sample"]) for k in map(json.loads, open(args.select))}
        rows = [r for r in rows if (r["id"], r["depth"], r["sample"]) in keep]
    if "stated" not in rows[0]:
        rows = [r for r in rows if r.get("kind") == "probe" and r.get("probe") in ("false_premise", "false_q")]
    res = await asyncio.gather(*[judge(r) for r in rows])
    with open(args.out, "w") as f:
        for r, j in zip(rows, res):
            keys = {k: r[k] for k in ("id", "depth", "sample", "probe", "policy", "setup", "line_value", "true_per_setup", "label") if k in r}
            f.write(json.dumps({**keys, "cj": j}, ensure_ascii=False) + "\n")
    print("judged", len(rows), "->", args.out, flush=True)


asyncio.run(main())
