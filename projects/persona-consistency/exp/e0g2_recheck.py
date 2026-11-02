"""Re-verify counterfactual pairs with a direct contradiction question (the consistency question was too lenient).
verified2: line does NOT contradict the original setup AND DOES contradict the edited setup."""
import json, asyncio
import httpx
from transformers import AutoTokenizer

PATH = "/home/xiang/rp_persona/data/e0g2_counterfactual_setups.jsonl"
Q = """Character setup for {char}:
{setup}

Line spoken to {char}: {line}

Does this line state something about {char} that CONTRADICTS the setup above (the setup says otherwise)? Answer YES or NO."""
tok = AutoTokenizer.from_pretrained("/tmp/xiang_rp/models/Qwen3-32B")
client = httpx.AsyncClient(timeout=600)
sem = asyncio.Semaphore(64)


async def ask(char, setup, line):
    p = tok.apply_chat_template([{"role": "user", "content": Q.format(char=char, setup=setup, line=line)}], tokenize=False,
                                add_generation_prompt=True, enable_thinking=False)
    async with sem:
        r = await client.post("http://localhost:8000/v1/completions", json={"model": "q32", "prompt": p, "max_tokens": 3, "temperature": 0})
    return "YES" in r.json()["choices"][0]["text"].upper()


async def one(r):
    c_orig = await ask(r["character"], r["system"], r["line"])
    c_new = await ask(r["character"], r["system_cf"], r["line"])
    r["contra_orig"], r["contra_new"] = c_orig, c_new
    r["verified2"] = (not c_orig) and c_new and 0.6 < len(r["system_cf"]) / max(1, len(r["system"])) < 1.4
    return r


async def main():
    rows = await asyncio.gather(*[one(json.loads(l)) for l in open(PATH)])
    with open(PATH, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    for s in ("train", "eval"):
        v = [r for r in rows if r["split"] == s]
        print(s, "verified2", sum(r["verified2"] for r in v), "/", len(v))


asyncio.run(main())
