"""Generate each slot's next line with one model (vLLM offline).

usage: gen.py MODEL_PATH TAG KIND(chat|base) [--generic]
--generic adds a control condition where the speaker is not named.
"""
import json
import re
import sys
from pathlib import Path

from vllm import LLM, SamplingParams

ROOT = Path.home() / "rp_voice"
model_path, tag, kind = sys.argv[1], sys.argv[2], sys.argv[3]
generic = "--generic" in sys.argv
slots = [json.loads(l) for l in open(ROOT / "data/slots/slots.jsonl")]

SYS_NAMED = ("You are a screenwriter continuing a script from {work}. Write only the next line spoken by {name}, "
             "in {name}'s own voice. Output just the spoken line: no name prefix, no quotes, no stage directions.")
SYS_GENERIC = ("You are a screenwriter continuing a script from {work}. Write only the next spoken line of dialogue. "
               "Output just the spoken line: no name prefix, no quotes, no stage directions.")


def chat_prompt(tok, s, named):
    sys_msg = (SYS_NAMED if named else SYS_GENERIC).format(work=s["work"], name=s["name"])
    user = "Script so far:\n" + "\n".join(s["context"]) + (f"\n\n{s['name']}:" if named else "\n\nNext line:")
    msgs = [{"role": "system", "content": sys_msg}, {"role": "user", "content": user}]
    kw = {"enable_thinking": False} if "qwen3" in tag.lower() else {}
    try:
        return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, **kw)
    except Exception:  # templates without a system role (Gemma folds it into the user turn itself)
        msgs = [{"role": "user", "content": sys_msg + "\n\n" + user}]
        return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, **kw)


def base_prompt(s):
    return f"The following is a scene from {s['work']}.\n\n" + "\n".join(s["context"]) + f"\n{s['name']}:"


def clean(text, name):
    for line in text.strip().splitlines():
        line = line.strip()
        if line:
            break
    else:
        return ""
    line = re.sub(rf"^\s*\**{re.escape(name)}\**\s*:\s*", "", line, flags=re.I)
    line = re.sub(r"\([^)]*\)|\[[^\]]*\]|\*[^*]*\*", "", line)
    return line.strip().strip('"“”').strip()


llm = LLM(model=model_path, dtype="bfloat16", max_model_len=4096, gpu_memory_utilization=0.85, seed=0)
tok = llm.get_tokenizer()
params = SamplingParams(temperature=0.7, top_p=0.9, max_tokens=80, seed=0,
                        stop=["\n"] if kind == "base" else None)
conds = ["named"] + (["generic"] if generic else [])
out = ROOT / "runs" / f"{tag}.jsonl"
with open(out, "w") as f:
    for cond in conds:
        if kind == "base":
            prompts = [base_prompt(s) for s in slots]
        else:
            prompts = [chat_prompt(tok, s, cond == "named") for s in slots]
        res = llm.generate(prompts, params)
        for s, r in zip(slots, res):
            raw = r.outputs[0].text
            f.write(json.dumps({"slot": s["slot"], "model": tag, "cond": cond, "raw": raw,
                                "text": clean(raw, s["name"])}, ensure_ascii=False) + "\n")
print("wrote", out)
