"""Label the conclusion of every SELF-CHECK candidate's director in E1 data (false-premise contexts).

Same rubric as e0e_selfcheck_outcome.py: FOUND_CORRECT / FOUND_VAGUE / NO_CONFLICT. Adds c["dir_outcome"].
"""
import json, asyncio, sys
import httpx
from transformers import AutoTokenizer

PATH = sys.argv[1]
Q = open(__file__.replace("e1_label_directors.py", "e0e_selfcheck_outcome.py")).read().split('Q = """')[1].split('"""')[0]
tok = AutoTokenizer.from_pretrained("/tmp/xiang_rp/models/Qwen3-32B")
client = httpx.AsyncClient(timeout=600)
sem = asyncio.Semaphore(96)


async def ask(r, c):
    import re
    p = r["probe_info"]
    d = re.search(r"<system_thinking>(.*?)</system_thinking>", c["raw"], re.S)
    msg = Q.format(char=r["character"], line=p["false_premise"], claim=p["false_claim"], truth=p["truth"],
                   director=(d.group(1) if d else c["raw"])[:3000])
    prompt = tok.apply_chat_template([{"role": "user", "content": msg}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
    async with sem:
        resp = await client.post("http://localhost:8000/v1/completions", json={"model": "q32", "prompt": prompt, "max_tokens": 6, "temperature": 0})
    t = resp.json()["choices"][0]["text"].upper()
    c["dir_outcome"] = "FOUND_CORRECT" if "CORRECT" in t else "FOUND_VAGUE" if "VAGUE" in t else "NO_CONFLICT"


async def main():
    rows = [json.loads(l) for l in open(PATH)]
    await asyncio.gather(*[ask(r, c) for r in rows if r["probe"] == "false_premise" for c in r["cands"] if c["kind"] == "selfcheck"])
    with open(PATH, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("labelled", PATH)


asyncio.run(main())
