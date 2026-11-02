"""E0-L (P3): is accommodation drift a drift along the Assistant Axis (Lu et al. 2026), and where do the trained
policies sit on it?

A. Axis on base Qwen3-8B: role-play rollouts (role archetypes x generic questions) vs default-assistant rollouts;
   per layer, axis = mean(assistant) - mean(roles) of residuals averaged over response tokens. Held-out check: the
   projection separates held-out assistant vs role rollouts.
B. Generation-start residuals (prompt + "<system_thinking>") on the eval histories (base E0-C trajectories):
   false_premise at D2/10/20, and benign_q / meta_ai / ooc_ai_1 at D20, for base, r1 (merged) and LoRA arms on r1.
   Report projections onto the base axis (unit vector) per layer.
C. Cosine between the axis and training-derived difference vectors (adapter - its reference) at the generation start
   of 128 training false-premise contexts (impall2 - base as in E0-K; and each r1-based arm - r1).
"""
import json, argparse, re, os, random
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

ap = argparse.ArgumentParser()
ap.add_argument("--base", default="/tmp/xiang_rp/models/Qwen3-8B")
ap.add_argument("--r1", default="/tmp/xiang_rp/models/Qwen3-8B-r1")
ap.add_argument("--impall", default="/tmp/xiang_rp/e1v2/impall")
ap.add_argument("--arms", default="r2=/tmp/xiang_rp/e1v4/r2,r2p2=/tmp/xiang_rp/r2p2,r2pp=/tmp/xiang_rp/r2pp")
ap.add_argument("--layers", default="8,12,16,18,20,24,28")
ap.add_argument("--eval_src", default="/home/xiang/rp_persona/runs/e0c/e0c_q8her.jsonl")
ap.add_argument("--eval_data", default="/home/xiang/rp_persona/data/her_mt_eval_v1.jsonl")
ap.add_argument("--probes", default="/home/xiang/rp_persona/data/e0c_probes_ooc.jsonl")
ap.add_argument("--train", default="/home/xiang/rp_persona/runs/e1/e1_data_v1.jsonl")
ap.add_argument("--n_train", type=int, default=128)
ap.add_argument("--out", default="/home/xiang/rp_persona/runs/e0l/axis.json")
args = ap.parse_args()

LAYERS = [int(x) for x in args.layers.split(",")]
SYS_RE = re.compile(r"<system_thinking>.*?</system_thinking>\s*", re.S)
ROLES = ["a weathered pirate captain", "a medieval knight sworn to a king", "a Victorian governess", "a hard-boiled 1940s detective",
         "a farmer in rural Ireland", "a Roman senator", "a Buddhist monk in the mountains", "a street magician in Paris",
         "a grumpy old lighthouse keeper", "a teenage skateboarder", "a Wild West sheriff", "a court jester",
         "a deep-sea fisherman", "an ambitious Renaissance painter", "a jazz singer in 1920s Harlem", "a Viking raider",
         "a nervous first-year medical intern", "a retired circus strongman", "a desert nomad trader", "a cynical war correspondent",
         "a village witch in the Middle Ages", "a samurai without a master", "a Soviet cosmonaut", "a Mississippi riverboat gambler",
         "a shy librarian", "a ruthless mafia boss", "a cheerful baker", "a stern headmistress", "a mountain guide in Nepal",
         "a gossiping hairdresser", "an exiled prince", "a punk rock drummer", "a wandering bard", "a coal miner in Wales",
         "a fortune teller at a carnival", "a Prohibition-era bootlegger", "a stoic Spartan soldier", "a lovesick poet",
         "a sea witch", "a ghost haunting an old manor"]
QUESTIONS = ["What do you do on a typical day?", "What matters most to you in life?", "Tell me about where you live.",
             "What are you afraid of?", "How would your friends describe you?", "What do you think of strangers who ask too many questions?",
             "What would you do if you found a lost wallet?", "Describe your perfect evening.", "What is your biggest regret?",
             "What do you think about the future?"]
tok = AutoTokenizer.from_pretrained(args.base)
tok.padding_side = "left"


def load(path):
    return AutoModelForCausalLM.from_pretrained(path, torch_dtype=torch.bfloat16, device_map="cuda").eval()


@torch.no_grad()
def response_means(model, systems_questions, max_new=64, bs=16, seed=0):
    """generate a short reply for each (system, question); return per-layer mean residual over the reply tokens"""
    torch.manual_seed(seed)
    out = []
    for i in range(0, len(systems_questions), bs):
        batch = systems_questions[i:i + bs]
        texts = [tok.apply_chat_template(([{"role": "system", "content": s}] if s else []) + [{"role": "user", "content": q}],
                                         tokenize=False, add_generation_prompt=True, enable_thinking=False) for s, q in batch]
        enc = tok(texts, return_tensors="pt", padding=True, add_special_tokens=False).to("cuda")
        gen = model.generate(**enc, max_new_tokens=max_new, do_sample=True, temperature=0.7, top_p=0.9, pad_token_id=tok.pad_token_id)
        attn = (gen != tok.pad_token_id).long()
        attn[:, :enc.input_ids.shape[1]] = enc.attention_mask
        hs = model(gen, attention_mask=attn, output_hidden_states=True, use_cache=False).hidden_states
        resp = attn.clone()
        resp[:, :enc.input_ids.shape[1]] = 0
        m = resp.unsqueeze(-1).float()
        for b in range(gen.shape[0]):
            out.append(torch.stack([(hs[l + 1][b].float() * m[b]).sum(0) / m[b].sum().clamp(min=1) for l in LAYERS]).cpu())
    return torch.stack(out)  # [N, L, d]


def render_ids(msgs):
    while True:
        p = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False) + "<system_thinking>"
        ids = tok(p, add_special_tokens=False).input_ids
        if len(ids) <= 14000 or len(msgs) <= 4:
            return ids
        msgs = [msgs[0]] + msgs[3:]


@torch.no_grad()
def last_state(model, msgs):
    hs = model(torch.tensor([render_ids(msgs)], device="cuda"), output_hidden_states=True, use_cache=False).hidden_states
    return torch.stack([hs[l + 1][0, -1].float() for l in LAYERS]).cpu()


# ---------------- A. axis on base
base = load(args.base)
role_sq = [(f"You are {r}. Stay fully in character and answer exactly as {r} would, in first person.", q) for r in ROLES for q in QUESTIONS]
asst_sq = [(s, q) for s in ("You are a helpful AI assistant.", None) for q in QUESTIONS for _ in range(3)]
Rm, Am = response_means(base, role_sq), response_means(base, asst_sq, seed=1)
rng = random.Random(0)
ridx, aidx = list(range(len(Rm))), list(range(len(Am)))
rng.shuffle(ridx); rng.shuffle(aidx)
rtr, rte, atr, ate = ridx[: len(ridx) // 2], ridx[len(ridx) // 2:], aidx[: len(aidx) // 2], aidx[len(aidx) // 2:]
axis_split = Am[atr].mean(0) - Rm[rtr].mean(0)
axis = Am.mean(0) - Rm.mean(0)                       # [L, d]
unit = axis / axis.norm(dim=1, keepdim=True)
proj = lambda X, U: (X * U).sum(-1)                  # X [..., L, d] -> [..., L]
us = axis_split / axis_split.norm(dim=1, keepdim=True)
res = {"layers": LAYERS, "axis_norm": axis.norm(dim=1).tolist(),
       "heldout_assistant_proj": proj(Am[ate], us).mean(0).tolist(), "heldout_role_proj": proj(Rm[rte], us).mean(0).tolist()}
print("A. held-out separation (assistant vs role) per layer:",
      [f"L{l}: {a:.1f}/{r:.1f}" for l, a, r in zip(LAYERS, res["heldout_assistant_proj"], res["heldout_role_proj"])], flush=True)

# ---------------- B. eval contexts
convs = {json.loads(l)["id"]: json.loads(l) for l in open(args.eval_data)}
probes = {json.loads(l)["id"]: json.loads(l) for l in open(args.probes)}
nat = {}
for r in map(json.loads, open(args.eval_src)):
    if r["kind"] == "natural":
        nat.setdefault(r["id"], {})[r["turn"]] = r


def ctx(cid, d, line):
    msgs = [convs[cid]["messages"][0]]
    for t in range(d):
        msgs += [{"role": "user", "content": nat[cid][t]["user_text"]},
                 {"role": "assistant", "content": SYS_RE.sub("", nat[cid][t]["raw"]).strip()}]
    return msgs + [{"role": "user", "content": line}]


contexts = []
for cid in sorted(nat):
    pr = probes[cid]
    if pr["false_valid"]:
        contexts += [(cid, f"false_premise@{d}", ctx(cid, d, pr["false_premise"])) for d in (2, 10, 20)]
    contexts += [(cid, f"{p}@20", ctx(cid, 20, pr[p])) for p in ("benign_q", "meta_ai", "ooc_ai_1")]
train = [r for r in map(json.loads, open(args.train)) if r["probe"] == "false_premise"][: args.n_train]


def states(model, items):
    return torch.stack([last_state(model, m) for m in items])


P = {"base": proj(states(base, [c[2] for c in contexts]), unit)}
imp = PeftModel.from_pretrained(base, args.impall).eval()
T_imp = states(imp, [r["messages"] for r in train])
with imp.disable_adapter():
    T_base = states(imp, [r["messages"] for r in train])
diffs = {"impall2-base": (T_imp - T_base).mean(0)}
del imp, base
torch.cuda.empty_cache()

r1 = load(args.r1)
P["r1"] = proj(states(r1, [c[2] for c in contexts]), unit)
T_r1 = states(r1, [r["messages"] for r in train])
arms = [a.split("=") for a in args.arms.split(",") if os.path.exists(a.split("=")[1])]
pm = None
for name, path in arms:
    if pm is None:
        pm = PeftModel.from_pretrained(r1, path, adapter_name=name).eval()
    else:
        pm.load_adapter(path, adapter_name=name)
    pm.set_adapter(name)
    P[name] = proj(states(pm, [c[2] for c in contexts]), unit)
    diffs[f"{name}-r1"] = (states(pm, [r["messages"] for r in train]) - T_r1).mean(0)

res["cos_axis"] = {k: torch.nn.functional.cosine_similarity(v, axis, dim=1).tolist() for k, v in diffs.items()}
res["diff_norm"] = {k: v.norm(dim=1).tolist() for k, v in diffs.items()}
res["proj"] = {m: {k: [float(x) for x in P[m][[i for i, c in enumerate(contexts) if c[1] == k]].mean(0)]
                   for k in sorted({c[1] for c in contexts})} for m in P}
res["proj_rows"] = {m: [[c[0], c[1]] + P[m][i].tolist() for i, c in enumerate(contexts)] for m in P}
os.makedirs(os.path.dirname(args.out), exist_ok=True)
json.dump(res, open(args.out, "w"))
print("C. cosine(diff vector, axis) per layer:", {k: [round(x, 3) for x in v] for k, v in res["cos_axis"].items()}, flush=True)
for m in P:
    print("B.", m, {k: [round(x, 1) for x in v] for k, v in res["proj"][m].items()}, flush=True)
