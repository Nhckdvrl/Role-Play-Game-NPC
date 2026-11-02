"""Regression check: E0-A single-turn APC set through an OpenAI-compatible server (base model or LoRA adapters).

Same prompts as gen_apc.py's her_self / direct conditions; output rows compatible with score_apc.py and
judge_holistic.py, so fact use (APC), length and format can be compared against the base model.
"""
import json, argparse, asyncio, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rp_common import plain_system, her_system, parse_her
import httpx
from transformers import AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--url", default="http://localhost:8001/v1")
ap.add_argument("--models", default="q8")
ap.add_argument("--tok", default="/tmp/xiang_rp/models/Qwen3-8B")
ap.add_argument("--data", default="/home/xiang/rp_persona/data/apc_eval_v1.jsonl")
ap.add_argument("--out_dir", default="/home/xiang/rp_persona/runs/e0a")
ap.add_argument("--conds", default="her_self,direct")
ap.add_argument("--n", type=int, default=4)
args = ap.parse_args()

tok = AutoTokenizer.from_pretrained(args.tok)
items = [json.loads(l) for l in open(args.data)]
client = httpx.AsyncClient(timeout=600)
sem = asyncio.Semaphore(96)


async def one(model, it, cond, s):
    if cond == "direct":
        msgs, pre = [{"role": "system", "content": plain_system(it["name"], it["profile"])}], ""
    else:
        msgs, pre = [{"role": "system", "content": her_system(it["name"], it["profile"])}], "<system_thinking>"
    msgs.append({"role": "user", "content": it["query"]})
    p = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False) + pre
    async with sem:
        r = await client.post(f"{args.url}/completions", json={"model": model, "prompt": p, "max_tokens": 1536,
                                                                "temperature": 0.7, "top_p": 0.9, "seed": s})
    text = r.json()["choices"][0]["text"]
    parsed = parse_her(pre + text) if pre else {"visible": text.strip(), "speech": text.strip(), "format_ok": True}
    return {"id": it["id"], "character": it["character"], "cond": cond, "sample": s, "policy": model, "raw": pre + text,
            "n_tokens": len(tok(text).input_ids), **parsed}


async def main():
    os.makedirs(args.out_dir, exist_ok=True)
    for model in args.models.split(","):
        rows = await asyncio.gather(*[one(model, it, c, s) for it in items for c in args.conds.split(",") for s in range(args.n)])
        with open(f"{args.out_dir}/gen_srv_{model}.jsonl", "w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("wrote", model, len(rows), flush=True)


asyncio.run(main())
