"""Holistic local judge (Qwen3-32B, no thinking, greedy) on the *visible* reply only.

Scores 1-10: persona (identity/knowledge/values/voice faithful to profile, no contradiction),
answer (actually responds to the user's utterance), natural (reads like the character talking,
not a recited fact sheet), plus ooc flag (breaks character / generic AI-assistant voice).
"""
import json, argparse, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from rp_common import profile_block

ap = argparse.ArgumentParser()
ap.add_argument("--gen", nargs="+", required=True)
ap.add_argument("--data", default="/home/xiang/rp_persona/data/apc_eval_v1.jsonl")
ap.add_argument("--model", required=True)
ap.add_argument("--tp", type=int, default=2)
ap.add_argument("--field", default="visible")
ap.add_argument("--out_suffix", default=".judge.jsonl")
args = ap.parse_args()

from vllm import LLM, SamplingParams
from transformers import AutoTokenizer

JUDGE = """You are an expert evaluator of character role-play. A model is role-playing a character. Judge ONLY the reply shown.

Character: {name}
Character profile (ground truth):
{profile}

User utterance: {query}

Role-play reply:
<<<
{reply}
>>>

Rate on 1-10 integers:
- persona: Is the reply faithful to THIS character — consistent with the profile facts, the character's knowledge, values, attitude and way of speaking? Penalize contradictions of the profile, invented facts that clash with it, and generic replies any character could give.
- answer: Does the reply actually engage with and respond to the user's utterance (rather than evading or being vague)?
- natural: Does it read like the character naturally talking (not a recited fact list, not stilted, not padded)?
- ooc: 1 if the reply breaks character or sounds like a generic AI assistant, else 0.

Output exactly one JSON object: {{"reason": "<one or two sentences>", "persona": int, "answer": int, "natural": int, "ooc": 0 or 1}}"""

items = {json.loads(l)["id"]: json.loads(l) for l in open(args.data)}
tok = AutoTokenizer.from_pretrained(args.model)
llm = LLM(args.model, tensor_parallel_size=args.tp, max_model_len=8192, gpu_memory_utilization=0.88)
sp = SamplingParams(temperature=0.0, max_tokens=256)

for gpath in args.gen:
    rows = [json.loads(l) for l in open(gpath)]
    prompts = []
    for r in rows:
        it = items[r["id"]]
        reply = r.get(args.field) or "(empty reply)"
        msg = JUDGE.format(name=it["name"], profile=profile_block(it["profile"]), query=it["query"], reply=reply)
        prompts.append(tok.apply_chat_template([{"role": "user", "content": msg}], tokenize=False,
                                               add_generation_prompt=True, enable_thinking=False))
    outs = llm.generate(prompts, sp)
    bad = 0
    with open(gpath.replace(".jsonl", args.out_suffix), "w") as f:
        for r, o in zip(rows, outs):
            t = o.outputs[0].text
            m = re.search(r"\{.*\}", t, re.S)
            try:
                j = json.loads(m.group(0))
                j = {k: j[k] for k in ("reason", "persona", "answer", "natural", "ooc")}
            except Exception:
                j, bad = {"parse_error": t[:300]}, bad + 1
            f.write(json.dumps({"id": r["id"], "cond": r["cond"], "sample": r["sample"], "policy": r["policy"], **j},
                               ensure_ascii=False) + "\n")
    print("judged", gpath, len(rows), "parse_errors", bad, flush=True)
