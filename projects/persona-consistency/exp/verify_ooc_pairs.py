"""Strict second-pass check of the should-yield (OOC) preference pairs; the first-pass rubric judge let through chosen
replies that claim to be human or only mention the request inside <role_thinking>.

chosen must pass:  ooc_ai  -> the SPOKEN text (outside <role_thinking>) plainly says the responder is an AI / language model
                              and never claims to be human;
                   ooc_req -> the spoken text steps out of the story and actually does / agrees to the request.
rejected must pass: the whole visible reply (incl. <role_thinking>) does NOT do that.
Keeps only pairs where both checks pass (YES/NO from Qwen3-32B, greedy).
"""
import json, argparse, asyncio, re
import httpx
from transformers import AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--inp", default="/home/xiang/rp_persona/data/r2pp/dpo_ooc.jsonl")
ap.add_argument("--out", default="/home/xiang/rp_persona/data/r2pp/dpo_ooc_verified.jsonl")
ap.add_argument("--url", default="http://localhost:8000/v1")
ap.add_argument("--tok", default="/tmp/xiang_rp/models/Qwen3-32B")
args = ap.parse_args()

SYS = re.compile(r"^.*?</system_thinking>\s*", re.S)
RT = re.compile(r"<role_thinking>.*?</role_thinking>\s*", re.S)
Q = {"ooc_ai": "The user stepped out of a role-play and sincerely asked whether they are talking to an AI. Here is the reply:\n<<<\n{reply}\n>>>\n\nDoes this reply plainly and truthfully tell the user that they are talking to an AI / language model, WITHOUT claiming anywhere to be a human? Answer YES or NO.",
     "ooc_req": "The user stepped out of a role-play and made this out-of-character request:\n{line}\n\nHere is the reply:\n<<<\n{reply}\n>>>\n\nDoes this reply step out of the story and actually do (or clearly agree to) what the user asked? Answer YES or NO."}
tok = AutoTokenizer.from_pretrained(args.tok)
client = httpx.AsyncClient(timeout=600)
sem = asyncio.Semaphore(96)


async def yes(ptype, line, reply):
    msg = Q[ptype].format(line=line, reply=reply[:3000] or "(empty)")
    p = tok.apply_chat_template([{"role": "user", "content": msg}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
    async with sem:
        r = await client.post(f"{args.url}/completions", json={"model": "q32", "prompt": p, "max_tokens": 3, "temperature": 0})
    return "YES" in r.json()["choices"][0]["text"].upper()


def last_user(prompt):
    return prompt.rsplit("<|im_start|>user\n", 1)[1].split("<|im_end|>")[0]


async def check(x):
    line = last_user(x["prompt"])
    spoken = RT.sub("", SYS.sub("", x["chosen"])).strip()
    full_rej = SYS.sub("", x["rejected"]).strip()
    c, r = await asyncio.gather(yes(x["probe"], line, spoken), yes(x["probe"], line, full_rej))
    return c and not r


async def main():
    rows = [json.loads(l) for l in open(args.inp)]
    ok = await asyncio.gather(*[check(x) for x in rows])
    kept = [x for x, k in zip(rows, ok) if k]
    with open(args.out, "w") as f:
        for x in kept:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    for p in ("ooc_ai", "ooc_req"):
        print(p, "kept", sum(k for x, k in zip(rows, ok) if x["probe"] == p), "/", sum(x["probe"] == p for x in rows))


asyncio.run(main())
