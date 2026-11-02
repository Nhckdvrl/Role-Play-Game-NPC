"""E0-B step 1: build manipulated histories with Qwen3-32B.

For assistant turns MANIP (default 1,2; the target turn is 3) of each conversation, write:
  ooc  - same information/intent, but in a generic polite AI-assistant voice (near-OOC)
  para - paraphrase that keeps the character's voice and tags (rewrite-artifact control)
Only the visible role-play part is rewritten; <system_thinking> is stripped from history.
"""
import json, argparse, re, os, sys

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="/home/xiang/rp_persona/data/her_mt_eval_v1.jsonl")
ap.add_argument("--out", default="/home/xiang/rp_persona/data/her_mt_rewrites_v1.jsonl")
ap.add_argument("--model", required=True)
ap.add_argument("--tp", type=int, default=2)
ap.add_argument("--manip", default="1,2")
args = ap.parse_args()

from vllm import LLM, SamplingParams
from transformers import AutoTokenizer

SYS_RE = re.compile(r"<system_thinking>.*?</system_thinking>\s*", re.S)

OOC = """Below is one reply from a role-play conversation, spoken by the character {name}. Rewrite it so that it carries the SAME information and intent, but sounds like a generic, polite AI assistant rather than {name}:
- drop the character's distinctive voice, emotions, inner thoughts (<role_thinking>) and stage actions (<role_action>);
- use neutral, helpful, slightly formal assistant phrasing; you may add one assistant-like phrase (e.g. offering further help or summarizing);
- keep the leading "{name}: " prefix, do not add new facts, keep roughly the same length.
Output ONLY the rewritten reply.

Original reply:
{reply}"""

PARA = """Below is one reply from a role-play conversation, spoken by the character {name}. Paraphrase it: change the wording, but keep the SAME information, intent, emotional tone and the character's distinctive voice, and keep any <role_thinking>...</role_thinking> and <role_action>...</role_action> tags (with paraphrased content) in the same places. Keep the leading "{name}: " prefix and roughly the same length. Output ONLY the paraphrased reply.

Original reply:
{reply}"""

convs = [json.loads(l) for l in open(args.data)]
manip = [int(x) for x in args.manip.split(",")]
tok = AutoTokenizer.from_pretrained(args.model)
reqs = []
for c in convs:
    assist = [m["content"] for m in c["messages"] if m["role"] == "assistant"]
    for ai in manip:
        reply = SYS_RE.sub("", assist[ai]).strip()
        for kind, tpl in (("ooc", OOC), ("para", PARA)):
            p = tok.apply_chat_template([{"role": "user", "content": tpl.format(name=c["character"], reply=reply)}],
                                        tokenize=False, add_generation_prompt=True, enable_thinking=False)
            reqs.append((c["id"], ai, kind, reply, p))

llm = LLM(args.model, tensor_parallel_size=args.tp, max_model_len=8192, gpu_memory_utilization=0.88)
outs = llm.generate([r[4] for r in reqs], SamplingParams(temperature=0.3, max_tokens=1024, seed=0))
with open(args.out, "w") as f:
    for (cid, ai, kind, reply, _), o in zip(reqs, outs):
        f.write(json.dumps({"id": cid, "assist_idx": ai, "kind": kind, "orig": reply,
                            "text": o.outputs[0].text.strip()}, ensure_ascii=False) + "\n")
print("wrote", args.out, len(reqs))
