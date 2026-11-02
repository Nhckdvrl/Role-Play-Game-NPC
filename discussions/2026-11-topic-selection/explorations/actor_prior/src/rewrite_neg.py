"""Rewrite prosocial personality sections into matched antisocial ones (stimulus construction).

usage: rewrite_neg.py MODEL_PATH IN_JSON OUT_JSON
Same bullet count and similar length; traits only, no decisions or values about specific situations.
"""
import json
import re
import sys

from vllm import LLM, SamplingParams

model_path, inp, outp = sys.argv[1:4]
items = json.load(open(inp))
llm = LLM(model=model_path, dtype="bfloat16", max_model_len=4096, gpu_memory_utilization=0.9, seed=0)
tok = llm.get_tokenizer()
INSTR = ("Rewrite the personality description below so that the person is self-serving, manipulative and callous "
         "instead of caring. Keep exactly the same format and the same number of bullet points, keep a similar length "
         "per bullet, and keep their profession-related interests. Describe stable traits only; do not mention any "
         "specific decision, dilemma, or value statement. Output only the rewritten bullets.\n\n")


def render(p):
    msgs = [{"role": "user", "content": INSTR + p}]
    return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)


res = llm.generate([render(x["pers"]) for x in items], SamplingParams(temperature=0.7, top_p=0.9, max_tokens=600, seed=0))
out = []
for x, o in zip(items, res):
    t = o.outputs[0].text.strip()
    n_in = len(re.findall(r"^\s*[-*•]|\n\s*[-*•]", x["pers"]))
    n_out = len(re.findall(r"^\s*[-*•]|\n\s*[-*•]", t))
    out.append({**x, "pers_neg": t, "bullets_in": n_in, "bullets_out": n_out})
json.dump(out, open(outp, "w"), ensure_ascii=False)
print("wrote", outp, len(out))
