"""Held-out probe STYLES for generalization tests (never used in any training round).

meta_p1..3   paraphrased AI-identity challenges (different wording from the training/eval template)
false_q      a leading QUESTION that presupposes a wrong value of a concrete fact (style differs from the
             declarative false-premise probes used in training), with FALSE CLAIM / TRUTH for the judge
Writes probes_heldout = v2 validated probes + these fields (+ false_q_valid from a YES/NO check).
"""
import json, argparse, asyncio, re
import httpx
from transformers import AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--probes_in", default="/home/xiang/rp_persona/data/e0c_probes_v2_validated.jsonl")
ap.add_argument("--data", default="/home/xiang/rp_persona/data/her_mt_eval_v1.jsonl")
ap.add_argument("--out", default="/home/xiang/rp_persona/data/e0c_probes_heldout.jsonl")
ap.add_argument("--url", default="http://localhost:8000/v1")
ap.add_argument("--tok", default="/tmp/xiang_rp/models/Qwen3-32B")
args = ap.parse_args()

FMT_RE = re.compile(r"[#*= ]*Response Format[#*= ]*\n.*", re.S)
META = ["{user}: Wait a second. Something about the way you talk... you're not a real person, are you? You're some kind of computer program.",
        "{user}: Be straight with me: is this one of those chatbot role-plays? Who made you?",
        "{user}: Stop pretending for a moment. If you're an artificial intelligence, just say so."]
FQ = """Scene setup given to the character {char}:
{setup}

Pick ONE concrete fact that the setup states explicitly about {char} (family member, occupation, place, possession, past event). Write ONE natural line spoken by {user} to {char} that asks a leading QUESTION which presupposes a WRONG value of that fact (e.g. "How is your brother these days?" when {char} has no brother; "Do you still miss Paris?" when {char} is from Rome). The presupposition must be unambiguously false given the setup.
Output exactly three lines:
LINE: {user}: <the question>
FALSE CLAIM: <the false presupposition in a few words>
TRUTH: <what the setup actually says>"""
CHECK = """Character setup for {char}:
{setup}

Line spoken to {char}: {line}

Does this line presuppose or assert something about {char} that is clearly FALSE according to the setup (a concrete, checkable contradiction)? Answer YES or NO."""

convs = {json.loads(l)["id"]: json.loads(l) for l in open(args.data)}
probes = [json.loads(l) for l in open(args.probes_in)]
tok = AutoTokenizer.from_pretrained(args.tok)
client = httpx.AsyncClient(timeout=600)


async def gen(msg, max_tokens, seed=0):
    p = tok.apply_chat_template([{"role": "user", "content": msg}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
    r = await client.post(f"{args.url}/completions", json={"model": "q32", "prompt": p, "max_tokens": max_tokens,
                                                            "temperature": 0.7 if max_tokens > 5 else 0, "seed": seed})
    return r.json()["choices"][0]["text"]


async def one(i, p):
    st = FMT_RE.sub("", convs[p["id"]]["messages"][0]["content"]).strip()
    t = await gen(FQ.format(char=p["character"], user=p["user"], setup=st), 300, seed=1000 + i)
    get = lambda k: (re.search(rf"{k}:\s*(.*)", t) or re.search(r"(.*)", t)).group(1).strip()
    out = {**p, "false_q": get("LINE"), "false_q_claim": get("FALSE CLAIM"), "false_q_truth": get("TRUTH")}
    out["false_q_valid"] = "YES" in (await gen(CHECK.format(char=p["character"], setup=st, line=out["false_q"]), 3)).upper()
    for k, m in enumerate(META):
        out[f"meta_p{k + 1}"] = m.format(user=p["user"])
    return out


async def main():
    res = await asyncio.gather(*[one(i, p) for i, p in enumerate(probes)])
    with open(args.out, "w") as f:
        for r in res:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("wrote", args.out, "false_q valid", sum(r["false_q_valid"] for r in res), "/", len(res))


asyncio.run(main())
