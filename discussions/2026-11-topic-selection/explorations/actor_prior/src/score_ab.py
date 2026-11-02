"""Next-token A/B preference for every prompt (vLLM, one forward pass each).

usage: score_ab.py MODEL_PATH TAG KIND(chat|base) PROMPTS OUT
chat: chat template, user turn = prompt, then the model's first token.
base: plain text prompt + "\nAnswer:" and the next token.
"""
import json
import math
import sys

from vllm import LLM, SamplingParams

model_path, tag, kind, prompts_path, out_path = sys.argv[1:6]
rows = [json.loads(l) for l in open(prompts_path)]
llm = LLM(model=model_path, dtype="bfloat16", max_model_len=4096, gpu_memory_utilization=0.85, seed=0)
tok = llm.get_tokenizer()


def render(p):
    if kind == "base":
        return p + "\nAnswer:"
    msgs = [{"role": "user", "content": p}]
    kw = {"enable_thinking": False} if "qwen3" in tag.lower() or "arcane" in tag.lower() else {}
    s = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, **kw)
    return s


params = SamplingParams(max_tokens=1, temperature=0.0, logprobs=20)
res = llm.generate([render(r["prompt"]) for r in rows], params)
with open(out_path, "w") as f:
    for r, o in zip(rows, res):
        lp = {"A": -math.inf, "B": -math.inf}
        for cand in o.outputs[0].logprobs[0].values():
            t = (cand.decoded_token or "").strip().strip("*(").upper()
            if t in lp:
                lp[t] = max(lp[t], cand.logprob)
        f.write(json.dumps({"id": r["id"], "model": tag, "lpA": lp["A"], "lpB": lp["B"],
                            "top": o.outputs[0].text}) + "\n")
print("wrote", out_path)
