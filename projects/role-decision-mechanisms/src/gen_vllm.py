"""Greedy generation for chat prompts. usage: gen_vllm.py MODEL TAG IN.jsonl OUT.jsonl [max_tokens]"""
import json, sys
from vllm import LLM, SamplingParams
model, tag, inp, out = sys.argv[1:5]
mt = int(sys.argv[5]) if len(sys.argv) > 5 else 160
rows = [json.loads(l) for l in open(inp)]
llm = LLM(model=model, dtype="bfloat16", max_model_len=8192, gpu_memory_utilization=0.85, seed=0, enforce_eager=True)
tok = llm.get_tokenizer()
kw = {"enable_thinking": False} if "qwen3" in tag.lower() else {}
texts = [tok.apply_chat_template(r["messages"], tokenize=False, add_generation_prompt=True, **kw) for r in rows]
res = llm.generate(texts, SamplingParams(max_tokens=mt, temperature=0.0))
with open(out, "w") as f:
    for r, o in zip(rows, res):
        f.write(json.dumps({"id": r["id"], "text": o.outputs[0].text}) + "\n")
print("wrote", out)
