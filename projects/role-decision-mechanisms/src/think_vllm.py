"""Qwen3 with thinking ON: generate, then read the final A/B answer after </think>.
usage: think_vllm.py MODEL TAG IN.jsonl OUT.jsonl"""
import json, re, sys
from vllm import LLM, SamplingParams
model, tag, inp, out = sys.argv[1:5]
rows = [json.loads(l) for l in open(inp)]
llm = LLM(model=model, dtype="bfloat16", max_model_len=8192, gpu_memory_utilization=0.85, seed=0)
tok = llm.get_tokenizer()
texts = [tok.apply_chat_template(r["messages"], tokenize=False, add_generation_prompt=True, enable_thinking=True) for r in rows]
res = llm.generate(texts, SamplingParams(max_tokens=3000, temperature=0.6, top_p=0.95, seed=0))
with open(out, "w") as f:
    for r, o in zip(rows, res):
        t = o.outputs[0].text
        ans = t.split("</think>")[-1] if "</think>" in t else ""
        m = re.findall(r"\b([AB])\b", ans)
        f.write(json.dumps({"id": r["id"], "answer": m[0] if m else None, "think_len": len(t.split("</think>")[0]), "text": t[-1500:]}) + "\n")
print("wrote", out)
