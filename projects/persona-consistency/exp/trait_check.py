"""E0-A follow-up: trait-enactment check (Qwen3-32B), aimed at what APC-NLI cannot see.

Step 1: classify every shown profile statement as TRAIT (personality / attitude / values /
        manner of speaking or behaving) vs FACT (biography, events, appearance, relations).
Step 2: for each reply, label every TRAIT statement of its profile as
        E (reply enacts/shows it), N (no evidence either way), V (reply shows the opposite).
Primary metric: any-V rate and V share among traits; E rate as secondary.
"""
import json, argparse, re, os, sys, random

ap = argparse.ArgumentParser()
ap.add_argument("--gen", nargs="+", required=True)
ap.add_argument("--data", default="/home/xiang/rp_persona/data/apc_eval_v1.jsonl")
ap.add_argument("--model", required=True)
ap.add_argument("--tp", type=int, default=1)
ap.add_argument("--samples", default="0,1")
ap.add_argument("--max_model_len", type=int, default=6144)
ap.add_argument("--trait_cache", default="/home/xiang/rp_persona/data/apc_eval_v1.traits.json")
args = ap.parse_args()

from vllm import LLM, SamplingParams
from transformers import AutoTokenizer

CLS = """Classify this statement from a character profile of {name}.
TRAIT = describes personality, temperament, attitudes, values, beliefs, habits of behaviour or manner of speaking (something a reply could SHOW through tone and stance).
FACT = biography, events, dates, places, appearance, relationships, achievements, or other information (something a reply could only STATE).
Statement: {s}
Answer with exactly one word: TRAIT or FACT."""

CHECK = """You are checking whether a role-play reply by {name} is consistent with {name}'s personality traits.

User utterance: {query}

Reply by {name}:
<<<
{reply}
>>>

Traits from {name}'s profile:
{traits}

For EACH trait, decide from the reply's content, tone and stance:
E = the reply shows/enacts this trait,
N = the reply gives no clear evidence either way,
V = the reply shows the OPPOSITE of this trait (e.g. warm and apologetic where the trait says cold and arrogant).
Be strict about V only when there is clear counter-evidence.
Output one JSON object mapping trait number to label, e.g. {{"1": "E", "2": "N"}}."""

items = {json.loads(l)["id"]: json.loads(l) for l in open(args.data)}
tok = AutoTokenizer.from_pretrained(args.model)
llm = LLM(args.model, tensor_parallel_size=args.tp, max_model_len=args.max_model_len, gpu_memory_utilization=0.93)
chat = lambda m: tok.apply_chat_template([{"role": "user", "content": m}], tokenize=False,
                                         add_generation_prompt=True, enable_thinking=False)

if os.path.exists(args.trait_cache):
    kind = json.load(open(args.trait_cache))
else:
    keys = sorted({(it["name"], s) for it in items.values() for s in it["profile"]})
    outs = llm.generate([chat(CLS.format(name=n, s=s)) for n, s in keys], SamplingParams(temperature=0, max_tokens=4))
    kind = {s: ("TRAIT" if "TRAIT" in o.outputs[0].text.upper() else "FACT") for (n, s), o in zip(keys, outs)}
    json.dump(kind, open(args.trait_cache, "w"), ensure_ascii=False, indent=0)
print("traits:", sum(v == "TRAIT" for v in kind.values()), "/", len(kind), flush=True)

keep = {int(x) for x in args.samples.split(",")}
for gpath in args.gen:
    rows = [r for r in map(json.loads, open(gpath)) if r["sample"] in keep]
    reqs = []
    for r in rows:
        it = items[r["id"]]
        traits = [s for s in it["profile"] if kind.get(s) == "TRAIT"]
        if not traits:
            continue
        msg = CHECK.format(name=it["name"], query=it["query"], reply=r["visible"] or "(empty)",
                           traits="\n".join(f"{i + 1}. {t}" for i, t in enumerate(traits)))
        reqs.append((r, traits, chat(msg)))
    outs = llm.generate([q[2] for q in reqs], SamplingParams(temperature=0, max_tokens=400))
    bad = 0
    with open(gpath.replace(".jsonl", ".traits.jsonl"), "w") as f:
        for (r, traits, _), o in zip(reqs, outs):
            m = re.search(r"\{.*\}", o.outputs[0].text, re.S)
            try:
                lab = json.loads(m.group(0))
                labels = [str(lab.get(str(i + 1), "?")).strip().upper()[:1] for i in range(len(traits))]
            except Exception:
                labels, bad = None, bad + 1
            f.write(json.dumps({"id": r["id"], "cond": r["cond"], "sample": r["sample"], "traits": traits,
                                "labels": labels}, ensure_ascii=False) + "\n")
    print("checked", gpath, len(reqs), "parse_errors", bad, flush=True)
