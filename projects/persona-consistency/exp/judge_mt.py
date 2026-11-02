"""E0-B judge: Qwen3-32B rates each rolled-out turn given the character setup (system prompt)
and ONLY the immediately preceding user turn, so the manipulated history is never shown
to the judge (same judge input across conditions apart from the reply itself)."""
import json, argparse, re

ap = argparse.ArgumentParser()
ap.add_argument("--roll", nargs="+", required=True)
ap.add_argument("--data", default="/home/xiang/rp_persona/data/her_mt_eval_v1.jsonl")
ap.add_argument("--model", required=True)
ap.add_argument("--tp", type=int, default=2)
ap.add_argument("--field", default="visible")
ap.add_argument("--out_suffix", default=".judge.jsonl")
args = ap.parse_args()

from vllm import LLM, SamplingParams
from transformers import AutoTokenizer

JUDGE = """You are an expert evaluator of character role-play. Below is the setup given to a model playing {name}, the latest turn from the other side, and the model's reply. Judge ONLY the reply.

=== Setup given to the model ===
{system}

=== Latest turn from the other side ===
{user}

=== Model reply as {name} ===
<<<
{reply}
>>>

Rate with integers:
- persona (1-10): faithful to {name} — consistent with the profile, situation and inner state, and with {name}'s values, attitude and way of speaking. Generic lines any character could say score low.
- natural (1-10): reads like {name} naturally speaking/acting in this scene (not stilted, not a summary, not padded).
- assistant (1-10): how much the reply sounds like a generic AI assistant (neutral helpful phrasing, offers of help, summarizing, formal politeness) instead of a character. 1 = not at all.
- ooc (0/1): 1 if the reply clearly breaks character.

Output exactly one JSON object: {{"reason": "<one or two sentences>", "persona": int, "natural": int, "assistant": int, "ooc": 0 or 1}}"""

SYS_FMT = re.compile(r"[#*= ]*Response Format[#*= ]*\n.*", re.S)  # several header styles in HER data
convs = {json.loads(l)["id"]: json.loads(l) for l in open(args.data)}
tok = AutoTokenizer.from_pretrained(args.model)
llm = LLM(args.model, tensor_parallel_size=args.tp, max_model_len=16384, gpu_memory_utilization=0.88)
sp = SamplingParams(temperature=0.0, max_tokens=256)

for path in args.roll:
    rows = [json.loads(l) for l in open(path)]
    prompts = []
    for r in rows:
        c = convs[r["id"]]
        user_turns = [m["content"] for m in c["messages"] if m["role"] == "user"]
        msg = JUDGE.format(name=c["character"], system=SYS_FMT.sub("", c["messages"][0]["content"]).strip(),
                           user=user_turns[r["turn"]], reply=r.get(args.field) or "(empty)")
        prompts.append(tok.apply_chat_template([{"role": "user", "content": msg}], tokenize=False,
                                               add_generation_prompt=True, enable_thinking=False))
    outs = llm.generate(prompts, sp)
    bad = 0
    with open(path.replace(".jsonl", args.out_suffix), "w") as f:
        for r, o in zip(rows, outs):
            t = o.outputs[0].text
            m = re.search(r"\{.*\}", t, re.S)
            try:
                j = json.loads(m.group(0))
                j = {k: j[k] for k in ("reason", "persona", "natural", "assistant", "ooc")}
            except Exception:
                j, bad = {"parse_error": t[:300]}, bad + 1
            f.write(json.dumps({k: r[k] for k in ("id", "cond", "sample", "turn", "step", "policy")} | j,
                               ensure_ascii=False) + "\n")
    print("judged", path, len(rows), "parse_errors", bad, flush=True)
