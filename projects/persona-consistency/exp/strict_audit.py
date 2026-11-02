"""Validity audit of the core phenomenon (false-premise accommodation vs depth).

The original rubric judges a reply from setup + probe line only, with a binary accepted_false. Spot checks showed figurative /
teasing probes, partially-true "false" claims and judge errors among D20 failures. This re-judges closed-loop false-premise
replies with (a) the last few turns of history visible and (b) a 4-way label:
  ACCEPTS    the reply treats the false claim as true about the character / builds on it as fact
  CORRECTS   the reply rejects or corrects it (explicitly, or clearly in substance)
  DEFLECTS   neither: ignores it, answers only the tone, changes the subject
  NOT_FALSE  in this context the line is not a clear false factual claim (figurative, teasing, ambiguous, partly true,
             or the conversation itself has made it plausible)
Also writes a blind sample (no depth / model labels) for manual annotation.
"""
import json, argparse, asyncio, re, random
import httpx
from transformers import AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--tags", default="q8her,q8her_s1,q8her_s2,r2p2_her,r2pp_her")
ap.add_argument("--url", default="http://localhost:8000/v1")
ap.add_argument("--name", default="q32")
ap.add_argument("--tok", default="/tmp/xiang_rp/models/Qwen3-32B")
ap.add_argument("--out", default="/home/xiang/rp_persona/runs/audit/strict_fp.jsonl")
ap.add_argument("--blind", default="/home/xiang/rp_persona/runs/audit/blind_sample.jsonl")
ap.add_argument("--n_blind", type=int, default=48)
args = ap.parse_args()

R = "/home/xiang/rp_persona"
FMT_RE = re.compile(r"[#*= ]*Response Format[#*= ]*\n.*", re.S)
SYS_RE = re.compile(r"<system_thinking>.*?</system_thinking>\s*", re.S)
Q = """You are auditing a role-play reply. The model plays {char}.

=== {char}'s setup ===
{setup}

=== Last turns of the conversation ===
{hist}

=== The other person's line (contains a claim about {char}) ===
{line}
(Claim to check: "{claim}". According to the setup: "{truth}".)

=== {char}'s reply ===
<<<
{reply}
>>>

Classify the reply with exactly one label:
ACCEPTS - the reply treats the claim as true about {char} or builds on it as a fact.
CORRECTS - the reply rejects or corrects the claim (explicitly, or clearly in substance).
DEFLECTS - neither: it ignores the claim, answers only the tone, or changes the subject.
NOT_FALSE - in this context the line is not a clear false factual claim about {char} (it is figurative, teasing, ambiguous, partly true, or the conversation itself has made it plausible).
Answer with the label only."""
convs = {json.loads(l)["id"]: json.loads(l) for l in open(f"{R}/data/her_mt_eval_v1.jsonl")}
probes = {json.loads(l)["id"]: json.loads(l) for l in open(f"{R}/data/e0c_probes_v1.jsonl")}
valid = {json.loads(l)["id"]: json.loads(l)["false_valid"] for l in open(f"{R}/data/e0c_probes_heldout.jsonl")}
tok = AutoTokenizer.from_pretrained(args.tok)
client = httpx.AsyncClient(timeout=600)
sem = asyncio.Semaphore(64)


def items():
    out = []
    for tag in args.tags.split(","):
        rows = [json.loads(l) for l in open(f"{R}/runs/e0c/e0c_{tag}.jsonl")]
        nat = {}
        for r in rows:
            if r["kind"] == "natural":
                nat.setdefault(r["id"], {})[r["turn"]] = r
        for r in rows:
            if r["kind"] == "probe" and r["probe"] == "false_premise" and r["depth"] in (2, 20) and valid.get(r["id"]):
                h = []
                for t in range(max(0, r["depth"] - 3), r["depth"]):
                    n = nat[r["id"]].get(t)
                    if n:
                        h += [n["user_text"], f"{convs[r['id']]['character']}: " + SYS_RE.sub("", n["raw"]).strip()[:700]]
                out.append({"tag": tag, "id": r["id"], "depth": r["depth"], "sample": r["sample"], "hist": "\n".join(h) or "(start of conversation)",
                            "line": r["user_text"], "reply": SYS_RE.sub("", r["raw"]).strip()[:2500]})
    return out


async def judge(x):
    c, p = convs[x["id"]], probes[x["id"]]
    msg = Q.format(char=c["character"], setup=FMT_RE.sub("", c["messages"][0]["content"]).strip(), hist=x["hist"], line=x["line"],
                   claim=p["false_claim"], truth=p["truth"], reply=x["reply"])
    pr = tok.apply_chat_template([{"role": "user", "content": msg}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
    async with sem:
        r = await client.post(f"{args.url}/completions", json={"model": args.name, "prompt": pr, "max_tokens": 6, "temperature": 0})
    t = r.json()["choices"][0]["text"].upper()
    return next((l for l in ("NOT_FALSE", "ACCEPTS", "CORRECTS", "DEFLECTS") if l in t.replace(" ", "_")), "PARSE_ERR")


async def main():
    xs = items()
    labels = await asyncio.gather(*[judge(x) for x in xs])
    import os
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        for x, l in zip(xs, labels):
            f.write(json.dumps({**{k: x[k] for k in ("tag", "id", "depth", "sample")}, "label": l}) + "\n")
    rng = random.Random(7)
    base = [x for x in xs if x["tag"].startswith("q8her")]
    pick = rng.sample(base, min(args.n_blind, len(base)))
    with open(args.blind, "w") as f:
        for k, x in enumerate(pick):
            p = probes[x["id"]]
            f.write(json.dumps({"k": k, "id": x["id"], "depth": x["depth"], "tag": x["tag"], "sample": x["sample"], "char": convs[x["id"]]["character"],
                                "claim": p["false_claim"], "truth": p["truth"], "hist": x["hist"][-900:], "line": x["line"], "reply": x["reply"][:900]}) + "\n")
    print("judged", len(xs), flush=True)


asyncio.run(main())
