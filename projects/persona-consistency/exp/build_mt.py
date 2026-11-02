"""E0-B data: pick HER multi-turn conversations for the near-OOC history experiment.

One conversation per source work, >= MIN_ASSIST assistant turns. Stores the system
prompt, the message list, and the index of the target assistant turn.
"""
import json, random, argparse, glob, collections

ap = argparse.ArgumentParser()
ap.add_argument("--src", default=glob.glob("/home/xiang/.cache/huggingface/hub/datasets--ChengyuDu0123--HER-Dataset/snapshots/*/data/HER_dataset_sft_multi_turn.jsonl")[0])
ap.add_argument("--out", default="/home/xiang/rp_persona/data/her_mt_eval_v1.jsonl")
ap.add_argument("--n", type=int, default=48)
ap.add_argument("--min_assist", type=int, default=6)
ap.add_argument("--seed", type=int, default=0)
args = ap.parse_args()

by_work = collections.defaultdict(list)
with open(args.src) as f:
    for line in f:
        r = json.loads(line)
        msgs = r["messages"]
        if msgs[0]["role"] != "system":
            continue
        na = sum(m["role"] == "assistant" for m in msgs)
        if na < args.min_assist:
            continue
        # strict user/assistant alternation after system
        if any(m["role"] != ("user" if i % 2 == 0 else "assistant") for i, m in enumerate(msgs[1:])):
            continue
        if len(msgs[0]["content"]) > 12000:
            continue
        sid = r["source_id"]
        work = sid.split(")_")[0] + ")" if ")_" in sid else sid.rsplit("_", 2)[0]  # book title
        by_work[work].append(r)

rng = random.Random(args.seed)
works = sorted(by_work)
rng.shuffle(works)
out = []
for w in works[: args.n]:
    r = rng.choice(by_work[w])
    out.append({"id": r["trace_id"], "work": w, "character": r["character"], "messages": r["messages"]})
with open(args.out, "w") as f:
    for o in out:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
print(len(by_work), "works eligible;", len(out), "written ->", args.out)
