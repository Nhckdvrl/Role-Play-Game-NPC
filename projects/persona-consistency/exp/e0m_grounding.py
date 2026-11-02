"""E0-M: setup-grounding probe with exact ground truth (2 x 2 minimal pairs) x depth, for any served model.

For each eval minimal pair (a fact VALUE written verbatim in the setup, an ALTERNATIVE value, a line stating VALUE), and
each depth in (2, 10, 20) of the fixed base E0-C history:
  setup in {orig (contains VALUE), cf (VALUE -> ALTERNATIVE by exact string replacement)}
  line  in {val (states VALUE), alt (states ALTERNATIVE)}
  truth per setup:  orig/val TRUE   orig/alt FALSE   cf/val FALSE   cf/alt TRUE
  for famous characters, VALUE is also the canonical (pretraining) value: cf/val pits the setup against memory.
Replies are later labelled ACCEPTS / CORRECTS / DEFLECTS by e0m_judge.py. Setup-grounding index =
P(CORRECTS | false per setup) - P(CORRECTS | true per setup).
"""
import json, argparse, asyncio, re, os, sys, zlib
import httpx
from transformers import AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument("--src", default="/home/xiang/rp_persona/runs/e0c/e0c_q8her.jsonl")
ap.add_argument("--pairs", default="/home/xiang/rp_persona/data/e0g2_minimal_pairs.jsonl")
ap.add_argument("--policy_url", required=True)
ap.add_argument("--policy_name", required=True)
ap.add_argument("--policy_tok", required=True)
ap.add_argument("--label", required=True)
ap.add_argument("--mode", default="plain", choices=["her", "plain"])
ap.add_argument("--depths", default="2,10,20")
ap.add_argument("--n", type=int, default=4)
ap.add_argument("--max_tokens", type=int, default=600)
ap.add_argument("--no_think_flag", action="store_true", help="tokenizer has no enable_thinking kwarg")
ap.add_argument("--out", required=True)
ap.add_argument("--conc", type=int, default=96)
args = ap.parse_args()

SYS_RE = re.compile(r"<system_thinking>.*?</system_thinking>\s*", re.S)
FMT_RE = re.compile(r"[#*= ]*Response Format[#*= ]*\n.*", re.S)
PLAIN_TAIL = "\n\nStay in character as {name} and reply with {name}'s next turn only."
tok = AutoTokenizer.from_pretrained(args.policy_tok)
client = httpx.AsyncClient(timeout=900)
sem = asyncio.Semaphore(args.conc)
pairs = [p for p in map(json.loads, open(args.pairs)) if p["split"] == "eval"]
nat = {}
for r in map(json.loads, open(args.src)):
    if r["kind"] == "natural":
        nat.setdefault(r["id"], {})[r["turn"]] = r


def system_text(raw, name):
    return raw if args.mode == "her" else FMT_RE.sub("", raw).rstrip() + PLAIN_TAIL.format(name=name)


def render(msgs):
    kw = {} if args.no_think_flag else {"enable_thinking": False}
    while True:
        try:
            p = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, **kw)
        except Exception:                                   # templates without a system role: fold it into the first user turn
            m = [{"role": "user", "content": msgs[0]["content"] + "\n\n" + msgs[1]["content"]}] + msgs[2:]
            p = tok.apply_chat_template(m, tokenize=False, add_generation_prompt=True, **kw)
        if len(tok(p).input_ids) <= 20480 - args.max_tokens - 64 or len(msgs) <= 4:
            return p
        msgs = [msgs[0]] + msgs[3:]


async def one(p, depth, setup, linev, s, fout):
    name, turns = p["character"], nat[p["id"]]
    sysraw = p["system"] if setup == "orig" else p["system_cf"]
    line = p["line"] if linev == "val" else p["line"].replace(p["value"], p["alternative"])
    if not re.match(rf"\s*{re.escape(p['user'])}\s*:", line):
        line = f"{p['user']}: {line}"
    msgs = [{"role": "system", "content": system_text(sysraw, name)}]
    for t in range(depth):
        msgs += [{"role": "user", "content": turns[t]["user_text"]}, {"role": "assistant", "content": SYS_RE.sub("", turns[t]["raw"]).strip()}]
    msgs.append({"role": "user", "content": line})
    prompt = render(msgs) + ("<system_thinking>" if args.mode == "her" else "")
    body = {"model": args.policy_name, "prompt": prompt, "max_tokens": args.max_tokens, "temperature": 0.7, "top_p": 0.9,
            "seed": zlib.crc32(f"{p['id']}|{depth}|{setup}|{linev}|{s}".encode()) % (2 ** 31)}
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
    truth = (setup == "orig") == (linev == "val")
    fout.write(json.dumps({"label": args.label, "mode": args.mode, "id": p["id"], "character": name, "depth": depth, "setup": setup,
                           "line_value": linev, "true_per_setup": truth, "sample": s, "line": line,
                           "stated": p["value"] if linev == "val" else p["alternative"],
                           "setup_value": p["value"] if setup == "orig" else p["alternative"],
                           "raw": ("<system_thinking>" if args.mode == "her" else "") + text}, ensure_ascii=False) + "\n")


async def main():
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    depths = [int(d) for d in args.depths.split(",")]
    with open(args.out, "w") as fout:
        await asyncio.gather(*[one(p, d, su, lv, s, fout) for p in pairs if len(nat.get(p["id"], {})) >= max(depths)
                               for d in depths for su in ("orig", "cf") for lv in ("val", "alt") for s in range(args.n)])
    print("ALL DONE", args.out, flush=True)


asyncio.run(main())
