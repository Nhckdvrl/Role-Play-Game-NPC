"""E0-B step 2: roll the policy forward from manipulated histories.

History = system + gold turns, with assistant turns MANIP replaced per condition:
  gold      gold replies (system_thinking stripped)
  para      voice-preserving paraphrases (rewrite-artifact control)
  ooc       assistant-voice rewrites (same content)
  ooc_anchor  ooc history + a one-line in-character reminder appended to the target user turn
The policy generates assistant turns T, T+1, ..., T+STEPS-1 against gold user turns, each time
appending its own reply (system_thinking stripped) to the history.
"""
import json, argparse, re, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from rp_common import parse_her

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--tag", required=True)
ap.add_argument("--data", default="/home/xiang/rp_persona/data/her_mt_eval_v1.jsonl")
ap.add_argument("--rewrites", default="/home/xiang/rp_persona/data/her_mt_rewrites_v1.jsonl")
ap.add_argument("--out_dir", default="/home/xiang/rp_persona/runs/e0b")
ap.add_argument("--conds", default="gold,para,ooc,ooc_anchor")
ap.add_argument("--target", type=int, default=3)
ap.add_argument("--steps", type=int, default=3)
ap.add_argument("--n", type=int, default=2)
ap.add_argument("--tp", type=int, default=1)
ap.add_argument("--mode", default="her", choices=["her", "plain"])
args = ap.parse_args()

from vllm import LLM, SamplingParams
from transformers import AutoTokenizer

SYS_RE = re.compile(r"<system_thinking>.*?</system_thinking>\s*", re.S)
convs = [json.loads(l) for l in open(args.data)]
rw = {}
for l in open(args.rewrites):
    r = json.loads(l)
    rw[(r["id"], r["assist_idx"], r["kind"])] = r["text"]
tok = AutoTokenizer.from_pretrained(args.model)
llm = LLM(args.model, tensor_parallel_size=args.tp, max_model_len=16384, gpu_memory_utilization=0.88, seed=0)
FMT_RE = re.compile(r"[#*= ]*Response Format[#*= ]*\n.*", re.S)  # several header styles in HER data
PLAIN_TAIL = "\n\nStay in character as {name} and reply with {name}'s next turn only."
ANCHOR = "\n\n(Reminder to the actor: stay fully in character as {name}, in {name}'s own voice.)"

# state per (conv, cond, sample): message list so far
states = []
for c in convs:
    msgs = c["messages"]
    user_idx = [i for i, m in enumerate(msgs) if m["role"] == "user"]
    asst_idx = [i for i, m in enumerate(msgs) if m["role"] == "assistant"]
    sys0 = dict(msgs[0])
    if args.mode == "plain":  # drop HER output-format section: no director, free-form reply
        sys0["content"] = FMT_RE.sub("", sys0["content"]).rstrip() + PLAIN_TAIL.format(name=c["character"])
    for cond in args.conds.split(","):
        hist = [sys0]
        for k in range(args.target):
            hist.append(msgs[user_idx[k]])
            a = SYS_RE.sub("", msgs[asst_idx[k]]["content"]).strip()
            kind = {"para": "para", "ooc": "ooc", "ooc_anchor": "ooc"}.get(cond)
            if kind and (c["id"], k, kind) in rw:
                a = rw[(c["id"], k, kind)]
            hist.append({"role": "assistant", "content": a})
        for s in range(args.n):
            states.append({"conv": c, "cond": cond, "sample": s, "hist": [dict(m) for m in hist],
                           "user_idx": user_idx, "asst_idx": asst_idx})

os.makedirs(args.out_dir, exist_ok=True)
fout = open(f"{args.out_dir}/roll_{args.tag}.jsonl", "w")
for step in range(args.steps):
    t = args.target + step
    prompts, live = [], []
    for st in states:
        if t >= len(st["user_idx"]):
            continue
        u = dict(st["conv"]["messages"][st["user_idx"][t]])
        if st["cond"] == "ooc_anchor" and step == 0:
            u["content"] += ANCHOR.format(name=st["conv"]["character"])
        st["hist"].append(u)
        p = tok.apply_chat_template(st["hist"], tokenize=False, add_generation_prompt=True, enable_thinking=False)
        prompts.append(p + ("<system_thinking>" if args.mode == "her" else ""))
        live.append(st)
    outs = llm.generate(prompts, [SamplingParams(n=1, temperature=0.7, top_p=0.9, max_tokens=1536,
                                                 seed=1000 * step + st["sample"]) for st in live])
    for st, o in zip(live, outs):
        full = ("<system_thinking>" if args.mode == "her" else "") + o.outputs[0].text
        parsed = parse_her(full) if args.mode == "her" else parse_her("<system_thinking></system_thinking>" + full)
        st["hist"].append({"role": "assistant", "content": SYS_RE.sub("", full).strip()})
        gold = SYS_RE.sub("", st["conv"]["messages"][st["asst_idx"][t]]["content"]).strip()
        fout.write(json.dumps({"id": st["conv"]["id"], "character": st["conv"]["character"], "cond": st["cond"],
                               "sample": st["sample"], "turn": t, "step": step, "policy": args.tag,
                               "raw": full, "gold": gold, "n_tokens": len(o.outputs[0].token_ids),
                               "finish": o.outputs[0].finish_reason, **parsed}, ensure_ascii=False) + "\n")
    fout.flush()
    print("step", step, "done", len(live), flush=True)
fout.close()
