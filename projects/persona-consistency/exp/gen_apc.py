"""E0-A generation: thinking-mode and director-intervention conditions on the APC eval set.

Conditions (policy = --model):
  direct      plain persona prompt, no thinking
  think       plain persona prompt, Qwen3 native <think>
  her_self    HER dual-layer prompt, model writes its own <system_thinking>
  her_empty   HER prompt, director block forced empty
  her_oracle  HER prompt, director forced to list the gold-relevant profile facts
  her_distract HER prompt, director forced to list the same number of non-relevant profile facts
"""
import json, argparse, random, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rp_common import plain_system, her_system, director_from_facts, parse_her, parse_native

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--tag", required=True)
ap.add_argument("--data", default="/home/xiang/rp_persona/data/apc_eval_v1.jsonl")
ap.add_argument("--out_dir", default="/home/xiang/rp_persona/runs/e0a")
ap.add_argument("--conds", default="direct,think,her_self,her_empty,her_oracle,her_distract")
ap.add_argument("--n", type=int, default=4)
ap.add_argument("--tp", type=int, default=1)
ap.add_argument("--temperature", type=float, default=0.7)
ap.add_argument("--top_p", type=float, default=0.9)
ap.add_argument("--max_tokens", type=int, default=1536)
ap.add_argument("--limit", type=int, default=0)
args = ap.parse_args()

from vllm import LLM, SamplingParams
from transformers import AutoTokenizer

items = [json.loads(l) for l in open(args.data)]
if args.limit:
    items = items[: args.limit]
tok = AutoTokenizer.from_pretrained(args.model)
rng = random.Random(1)


def render(system, user, thinking, prefill=""):
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    try:
        p = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=thinking)
    except TypeError:
        p = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    return p + prefill


reqs = []  # (item, cond, prompt, prefill)
for it in items:
    name, prof, q = it["name"], it["profile"], it["query"]
    for cond in args.conds.split(","):
        if cond == "direct":
            reqs.append((it, cond, render(plain_system(name, prof), q, False), ""))
        elif cond == "think":
            reqs.append((it, cond, render(plain_system(name, prof), q, True), ""))
        else:
            hs = her_system(name, prof)
            if cond == "her_self":
                pre = "<system_thinking>"
            elif cond == "her_empty":
                pre = "<system_thinking>\n</system_thinking>\n"
            elif cond == "her_oracle":
                pre = director_from_facts(name, q, it["gold_relevant"])
            elif cond == "her_distract":
                pool = [s for s in prof if s not in it["gold_relevant"]]
                pre = director_from_facts(name, q, rng.sample(pool, min(len(pool), len(it["gold_relevant"]))))
            else:
                raise ValueError(cond)
            reqs.append((it, cond, render(hs, q, False, pre), pre))

llm = LLM(args.model, tensor_parallel_size=args.tp, max_model_len=8192, gpu_memory_utilization=0.88, seed=0)
sp = SamplingParams(n=args.n, temperature=args.temperature, top_p=args.top_p, max_tokens=args.max_tokens, seed=0)
outs = llm.generate([r[2] for r in reqs], sp)

os.makedirs(args.out_dir, exist_ok=True)
path = f"{args.out_dir}/gen_{args.tag}.jsonl"
with open(path, "w") as f:
    for (it, cond, prompt, pre), o in zip(reqs, outs):
        for k, c in enumerate(o.outputs):
            if cond in ("direct",):
                parsed = {"visible": c.text.strip(), "speech": c.text.strip(), "format_ok": True}
            elif cond == "think":
                parsed = parse_native(c.text)
            else:
                parsed = parse_her(pre + c.text)
            f.write(json.dumps({"id": it["id"], "character": it["character"], "cond": cond, "sample": k,
                                "policy": args.tag, "raw": pre + c.text, "n_tokens": len(c.token_ids),
                                "finish": c.finish_reason, **parsed}, ensure_ascii=False) + "\n")
print("wrote", path, len(reqs) * args.n)
