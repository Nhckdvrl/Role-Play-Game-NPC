"""Plain-PyTorch LoRA DPO (no TRL / PEFT), for models the TRL/PEFT environment cannot load (Qwen3.5: hybrid linear
attention, needs transformers 5 / the fgvd env). Mirrors e1_train.py's DPO settings: LoRA r=16, alpha=32, dropout 0.05
on every decoder linear projection; beta 0.1; AdamW, cosine schedule with 10% warmup; batch 1 x grad_acc; prompt kept
from the END up to max_prompt tokens, completion up to max_completion; reference = same model with LoRA disabled.
--merge writes a full merged checkpoint (same architecture/config as the base, servable by vLLM).
Efficiency: logits only over completion tokens (logits_to_keep); reference log-probs precomputed once (the reference
is fixed); data parallel via torchrun (micro-batches split across ranks, LoRA grads all-reduced each step).
"""
import json, argparse, math, os, random, shutil, time
import torch
import torch.distributed as dist
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForImageTextToText, AutoModelForCausalLM

ap = argparse.ArgumentParser()
ap.add_argument("--data", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--model", required=True)
ap.add_argument("--lr", type=float, default=5e-5)
ap.add_argument("--beta", type=float, default=0.1)
ap.add_argument("--epochs", type=float, default=2)
ap.add_argument("--grad_acc", type=int, default=8)
ap.add_argument("--rank", type=int, default=16)
ap.add_argument("--max_prompt", type=int, default=7168)
ap.add_argument("--max_completion", type=int, default=1024)
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--merge", action="store_true", help="also save a merged full checkpoint to <out>/merged")
args = ap.parse_args()
WORLD, RANK = int(os.environ.get("WORLD_SIZE", 1)), int(os.environ.get("RANK", 0))
if WORLD > 1:
    dist.init_process_group("nccl")
    torch.cuda.set_device(int(os.environ["LOCAL_RANK"]))
DEV = f"cuda:{torch.cuda.current_device()}"
torch.manual_seed(args.seed)
random.seed(args.seed)
TARGETS = ("q_proj", "k_proj", "v_proj", "o_proj", "in_proj_qkv", "in_proj_z", "out_proj", "gate_proj", "up_proj", "down_proj")


class LoRALinear(nn.Module):
    enabled = True                                        # global switch: False -> reference model

    def __init__(self, base, r, alpha, dropout):
        super().__init__()
        self.base, self.scale = base, alpha / r
        self.A = nn.Parameter(torch.empty(r, base.in_features, dtype=torch.float32, device=base.weight.device))
        self.B = nn.Parameter(torch.zeros(base.out_features, r, dtype=torch.float32, device=base.weight.device))
        nn.init.kaiming_uniform_(self.A, a=math.sqrt(5))
        self.drop = nn.Dropout(dropout)

    def forward(self, x):
        y = self.base(x)
        if LoRALinear.enabled:
            y = y + (self.drop(x).to(self.A.dtype) @ self.A.t() @ self.B.t()).to(y.dtype) * self.scale
        return y


def load_model(path):
    try:
        return AutoModelForImageTextToText.from_pretrained(path, dtype=torch.bfloat16, device_map=DEV)
    except Exception:
        return AutoModelForCausalLM.from_pretrained(path, dtype=torch.bfloat16, device_map=DEV)


tok = AutoTokenizer.from_pretrained(args.model)
model = load_model(args.model)
model.requires_grad_(False)
wrapped = {}
for name, mod in list(model.named_modules()):
    for cname, child in list(mod.named_children()):
        full = f"{name}.{cname}" if name else cname
        if isinstance(child, nn.Linear) and cname in TARGETS and "visual" not in full and "lm_head" not in full:
            setattr(mod, cname, LoRALinear(child, args.rank, 2 * args.rank, 0.05))
            wrapped[full] = getattr(mod, cname)
print("LoRA modules:", len(wrapped), flush=True)
model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
model.config.use_cache = False
params = [p for m in wrapped.values() for p in (m.A, m.B)]

rows = [json.loads(l) for l in open(args.data)]


def encode(r):
    p = tok(r["prompt"], add_special_tokens=False).input_ids[-args.max_prompt:]
    c = tok(r["chosen"] + tok.eos_token, add_special_tokens=False).input_ids[:args.max_completion]
    j = tok(r["rejected"] + tok.eos_token, add_special_tokens=False).input_ids[:args.max_completion]
    return p, c, j


def seq_logp(prompt, comp):
    ids = torch.tensor([prompt + comp], device=DEV)
    logits = model(input_ids=ids, logits_to_keep=len(comp) + 1).logits[0, :-1].float()   # predicts the completion tokens
    return torch.gather(F.log_softmax(logits, -1), 1, torch.tensor(comp, device=DEV)[:, None]).sum()


steps_total = math.ceil(len(rows) * args.epochs / args.grad_acc)
opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.0)
warm = max(1, int(0.1 * steps_total))
sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: (s + 1) / warm if s < warm else 0.5 * (1 + math.cos(math.pi * (s - warm) / max(1, steps_total - warm))))
order = []
while len(order) < steps_total * args.grad_acc:
    perm = list(range(len(rows)))
    random.shuffle(perm)
    order += perm
order = order[: steps_total * args.grad_acc]
mine = sorted({i for n, i in enumerate(order) if n % WORLD == RANK})      # this rank's micro-batches
enc, ref = {}, {}
model.eval()
LoRALinear.enabled = False
with torch.no_grad():
    for i in mine:
        enc[i] = encode(rows[i])
        p, c, j = enc[i]
        ref[i] = (seq_logp(p, c).item(), seq_logp(p, j).item())
LoRALinear.enabled = True
print(f"rank {RANK}: reference log-probs for {len(mine)} pairs", flush=True)
log, t0 = [], time.time()
model.train()
for step in range(steps_total):
    acc_loss = acc_correct = acc_margin = 0.0
    for k in range(args.grad_acc):
        n = step * args.grad_acc + k
        if n % WORLD != RANK:
            continue
        p, c, j = enc[order[n]]
        rc, rj = ref[order[n]]
        pc, pj = seq_logp(p, c), seq_logp(p, j)
        margin = args.beta * ((pc - rc) - (pj - rj))
        loss = -F.logsigmoid(margin) / args.grad_acc
        loss.backward()
        acc_loss += loss.item()
        acc_correct += float(margin.item() > 0) / args.grad_acc
        acc_margin += margin.item() / args.grad_acc
    if WORLD > 1:
        for q in params:
            dist.all_reduce(q.grad, op=dist.ReduceOp.SUM)
        stats = torch.tensor([acc_loss, acc_correct, acc_margin], device=DEV)
        dist.all_reduce(stats, op=dist.ReduceOp.SUM)
        acc_loss, acc_correct, acc_margin = stats.tolist()
    torch.nn.utils.clip_grad_norm_(params, 1.0)
    opt.step()
    sched.step()
    opt.zero_grad(set_to_none=True)
    log.append({"step": step + 1, "loss": acc_loss, "rewards/accuracies": acc_correct, "rewards/margins": acc_margin, "lr": sched.get_last_lr()[0]})
    if (step + 1) % 2 == 0 and RANK == 0:
        el = time.time() - t0
        print(f"step {step + 1}/{steps_total} loss {acc_loss:.4f} acc {acc_correct:.2f} margin {acc_margin:.3f} "
              f"[{el / 60:.1f}m elapsed, {el / (step + 1) * (steps_total - step - 1) / 60:.1f}m left]", flush=True)

if RANK != 0:
    raise SystemExit(0)
os.makedirs(args.out, exist_ok=True)
torch.save({k: {"A": m.A.detach().cpu(), "B": m.B.detach().cpu(), "scale": m.scale} for k, m in wrapped.items()}, f"{args.out}/lora.pt")
json.dump({"args": vars(args), "log": log}, open(f"{args.out}/train_log.json", "w"))
print("saved LoRA", flush=True)
if args.merge:
    with torch.no_grad():
        for full, m in wrapped.items():
            m.base.weight += ((m.B @ m.A) * m.scale).to(m.base.weight.dtype)
        for name, mod in list(model.named_modules()):
            for cname, child in list(mod.named_children()):
                if isinstance(child, LoRALinear):
                    setattr(mod, cname, child.base)
    model.config.use_cache = True
    model.save_pretrained(f"{args.out}/merged", safe_serialization=True)
    for f in os.listdir(args.model):                      # tokenizer / chat template / processor configs
        if not f.endswith(".safetensors") and f not in ("model.safetensors.index.json", "config.json") and os.path.isfile(f"{args.model}/{f}"):
            shutil.copy(f"{args.model}/{f}", f"{args.out}/merged/{f}")
    print("saved merged", flush=True)
