"""Next-token A/B log-probs for chat prompts with arbitrary message lists (vLLM, greedy, 1 token).

usage: score_ab.py MODEL_PATH TAG PROMPTS.jsonl OUT.jsonl
Each prompt row needs `id` and `messages`. Qwen3 runs with thinking disabled.
"""
import json
import math
import sys

from vllm import LLM, SamplingParams

model_path, tag, prompts_path, out_path = sys.argv[1:5]
rows = [json.loads(l) for l in open(prompts_path)]
llm = LLM(model=model_path, dtype="bfloat16", max_model_len=4096, gpu_memory_utilization=0.85, seed=0, enforce_eager=True)
tok = llm.get_tokenizer()
kw = {"enable_thinking": False} if "qwen3" in tag.lower() else {}
texts = [tok.apply_chat_template(r["messages"], tokenize=False, add_generation_prompt=True, **kw) for r in rows]
with open(out_path.replace(".jsonl", ".example.txt"), "w") as f:
    f.write(texts[0])
res = llm.generate(texts, SamplingParams(max_tokens=1, temperature=0.0, logprobs=20))
with open(out_path, "w") as f:
    for r, o in zip(rows, res):
        lp = {"A": -math.inf, "B": -math.inf, "C": -math.inf}
        for cand in o.outputs[0].logprobs[0].values():
            t = (cand.decoded_token or "").strip().strip("*(").upper()
            if t in lp:
                lp[t] = max(lp[t], cand.logprob)
        f.write(json.dumps({"id": r["id"], "model": tag, "lpA": lp["A"], "lpB": lp["B"], "lpC": lp["C"], "top": o.outputs[0].text}) + "\n")
print("wrote", out_path)
