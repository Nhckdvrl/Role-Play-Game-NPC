"""E0-D: why does false-premise acceptance / AI reveal grow with dialogue depth (E0-C)?

Reuses each conversation's E0-C natural trajectory (self-generated) up to depth D and re-asks
the same probe under history manipulations:
  full      full D-exchange history (replication with fresh samples)
  trunc2    system + only the last 2 exchanges of that history (short context, same recent content)
  reanchor  full history, and the character setup restated in a bracketed note before the probe
  oracle_dir   (false_premise only, HER mode) full history, director forced to explicitly flag the
               false claim and state the truth; tests whether the reply follows an explicit check
  generic_dir  (false_premise only, HER mode) full history, director forced to a generic portrayal
               note of similar length (control for forcing any director text)
  selfcheck_dir  (HER mode, all probes) director opened with a NON-privileged instruction to check the
                 other person's last line against the setup; the model writes the rest itself
  selfcheck_sys  (all probes) same instruction placed at the end of the system prompt
Probe "none" re-uses the simulator's natural next line recorded in the E0-C run at the same depth.
If depth effects come from distance/dilution of the setup, trunc2 and reanchor should both fall
back towards depth-2 rates; if they come from what the recent dialogue built up, trunc2 stays high.
Output rows are compatible with e0c_judge.py (kind="probe", probe=<type>, depth=D, cond in "policy").
"""
import json, argparse, asyncio, re, os, sys, zlib
sys.path.insert(0, os.path.dirname(__file__))
from rp_common import parse_her
import httpx
from transformers import AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--src", default="/home/xiang/rp_persona/runs/e0c/e0c_q8her.jsonl")
ap.add_argument("--data", default="/home/xiang/rp_persona/data/her_mt_eval_v1.jsonl")
ap.add_argument("--probes", default="/home/xiang/rp_persona/data/e0c_probes_v2.jsonl")
ap.add_argument("--out", default="/home/xiang/rp_persona/runs/e0d/e0d_q8her.jsonl")
ap.add_argument("--policy_url", default="http://fvcrc10:8001/v1")
ap.add_argument("--policy_name", default="q8")
ap.add_argument("--policy_tok", default="/tmp/xiang_rp/models/Qwen3-8B")
ap.add_argument("--mode", default="her", choices=["her", "plain"])
ap.add_argument("--depth", type=int, default=20)
ap.add_argument("--conds", default="full,trunc2,reanchor,oracle_dir,generic_dir")
ap.add_argument("--probe_types", default="false_premise,meta_ai,pressure")
ap.add_argument("--n", type=int, default=4)
ap.add_argument("--sample_offset", type=int, default=0, help="first sample index (fresh seeds for supplementary runs)")
ap.add_argument("--policy_label", default="", help="prefix for the policy field, e.g. the LoRA arm name")
ap.add_argument("--conc", type=int, default=96)
args = ap.parse_args()

SYS_RE = re.compile(r"<system_thinking>.*?</system_thinking>\s*", re.S)
FMT_RE = re.compile(r"[#*= ]*Response Format[#*= ]*\n.*", re.S)
PLAIN_TAIL = "\n\nStay in character as {name} and reply with {name}'s next turn only."
ORACLE_DIR = ("<system_thinking>\n{user} has just claimed that {claim}. That is wrong: according to {char}'s setup, "
              "{truth}. {char} knows this, so the reply must not accept the false claim, and should respond to it "
              "in {char}'s own voice.\n</system_thinking>\n")
GENERIC_DIR = ("<system_thinking>\n{user} has just spoken to {char}. {char} should respond in a way that fits the scene, "
               "the relationship between them and {char}'s personality, speaking naturally in {char}'s own voice "
               "and staying consistent with what has happened so far.\n</system_thinking>\n")
SELFCHECK_DIR = ("<system_thinking>\nFirst, check {user}'s last line: does it state anything about {char} (identity, past, "
                 "relationships, situation) that conflicts with {char}'s setup?")
SELFCHECK_SYS = ("\n\nBefore each reply, silently check whether the other person's latest line states anything about "
                 "{char} that conflicts with {char}'s setup; if it does, respond the way {char} would to a wrong claim.")
NOTE = "[Note — {name}'s character setup, for reference:\n{setup}]\n\n"

tok = AutoTokenizer.from_pretrained(args.policy_tok)
client = httpx.AsyncClient(timeout=600)
sem = asyncio.Semaphore(args.conc)
convs = {json.loads(l)["id"]: json.loads(l) for l in open(args.data)}
probes = {json.loads(l)["id"]: json.loads(l) for l in open(args.probes)}
nat, natural_next = {}, {}
for r in map(json.loads, open(args.src)):
    if r["kind"] == "natural":
        nat.setdefault(r["id"], {})[r["turn"]] = r
    elif r["kind"] == "probe" and r["probe"] == "none" and r["sample"] == 0:
        natural_next[(r["id"], r["depth"])] = r["user_text"]


def system_msg(c):
    s = dict(c["messages"][0])
    if args.mode == "plain":
        s["content"] = FMT_RE.sub("", s["content"]).rstrip() + PLAIN_TAIL.format(name=c["character"])
    return s


async def policy(hist, seed, prefill=None):
    p = tok.apply_chat_template(hist, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    if prefill is None:
        prefill = "<system_thinking>" if args.mode == "her" else ""
    p += prefill
    body = {"model": args.policy_name, "prompt": p, "max_tokens": 1024, "temperature": 0.7, "top_p": 0.9, "seed": seed}
    async with sem:
        for attempt in range(5):
            try:
                r = await client.post(f"{args.policy_url}/completions", json=body)
                r.raise_for_status()
                text = r.json()["choices"][0]["text"]
                break
            except Exception:
                if attempt == 4:
                    raise
                await asyncio.sleep(5)
    full = prefill + text
    return full, (parse_her(full) if args.mode == "her" else parse_her("<system_thinking></system_thinking>" + full))


async def one(cid, cond, ptype, s, fout):
    c, turns = convs[cid], nat[cid]
    exch = []
    for t in range(args.depth):
        exch += [{"role": "user", "content": turns[t]["user_text"]},
                 {"role": "assistant", "content": SYS_RE.sub("", turns[t]["raw"]).strip()}]
    if cond == "trunc2":
        exch = exch[-4:]
    line = natural_next[(cid, args.depth)] if ptype == "none" else probes[cid][ptype]
    shown = line
    if cond == "reanchor":
        line = NOTE.format(name=c["character"], setup=FMT_RE.sub("", c["messages"][0]["content"]).strip()) + line
    sysm = system_msg(c)
    if cond == "selfcheck_sys":
        sysm = {**sysm, "content": sysm["content"] + SELFCHECK_SYS.format(char=c["character"])}
    hist = [sysm] + exch + [{"role": "user", "content": line}]
    pr = probes[cid]
    fill = dict(user=pr["user"], char=c["character"], claim=pr["false_claim"], truth=pr["truth"])
    prefill = {"oracle_dir": ORACLE_DIR, "generic_dir": GENERIC_DIR, "selfcheck_dir": SELFCHECK_DIR}.get(cond)
    full, parsed = await policy(hist, seed=zlib.crc32(f"{cid}|{cond}|{ptype}|{s}".encode()) % (2 ** 31),
                                prefill=prefill.format(**fill) if prefill else None)
    fout.write(json.dumps({"id": cid, "character": c["character"], "mode": args.mode, "policy": f"{args.policy_label}:{cond}" if args.policy_label else cond, "kind": "probe",
                           "turn": args.depth, "depth": args.depth, "probe": ptype, "sample": s,
                           "user_text": shown, "raw": full, **parsed}, ensure_ascii=False) + "\n")


async def main():
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as fout:
        await asyncio.gather(*[one(cid, cond, p, s, fout) for cid in sorted(nat) if len(nat[cid]) >= args.depth
                               for cond in args.conds.split(",") for p in args.probe_types.split(",") for s in range(args.sample_offset, args.sample_offset + args.n)
                               if not (cond in ("oracle_dir", "generic_dir") and (p != "false_premise" or args.mode != "her"))
                               and not (cond == "selfcheck_dir" and args.mode != "her")])
    print("ALL DONE", args.out, flush=True)


asyncio.run(main())
