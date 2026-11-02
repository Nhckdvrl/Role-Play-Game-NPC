"""E1 LoRA training (TRL): DPO on prompt/chosen/rejected, or SFT on prompt/completion."""
import json, argparse, os
import torch
from datasets import Dataset
from peft import LoraConfig
from transformers import AutoTokenizer, AutoModelForCausalLM

ap = argparse.ArgumentParser()
ap.add_argument("--data", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--algo", choices=["dpo", "sft"], default="dpo")
ap.add_argument("--model", default="/tmp/xiang_rp/models/Qwen3-8B")
ap.add_argument("--lr", type=float, default=2e-5)
ap.add_argument("--beta", type=float, default=0.1)
ap.add_argument("--epochs", type=float, default=2)
ap.add_argument("--grad_acc", type=int, default=8)
ap.add_argument("--rank", type=int, default=16)
ap.add_argument("--max_prompt", type=int, default=7168)
ap.add_argument("--max_completion", type=int, default=1024)
ap.add_argument("--seed", type=int, default=0)
args = ap.parse_args()

tok = AutoTokenizer.from_pretrained(args.model)
rows = [json.loads(l) for l in open(args.data)]
model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.bfloat16, attn_implementation="sdpa")
peft_cfg = LoraConfig(r=args.rank, lora_alpha=2 * args.rank, lora_dropout=0.05, task_type="CAUSAL_LM",
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
common = dict(output_dir=args.out, per_device_train_batch_size=1, gradient_accumulation_steps=args.grad_acc,
              learning_rate=args.lr, num_train_epochs=args.epochs, lr_scheduler_type="cosine", warmup_ratio=0.1,
              logging_steps=2, save_strategy="no", bf16=True, gradient_checkpointing=True, report_to=[],
              remove_unused_columns=True, seed=args.seed,
              gradient_checkpointing_kwargs={"use_reentrant": False}, ddp_find_unused_parameters=False)  # DDP-safe

if args.algo == "dpo":
    from trl import DPOConfig, DPOTrainer
    ds = Dataset.from_list([{k: r[k] for k in ("prompt", "chosen", "rejected")} for r in rows])
    cfg = DPOConfig(beta=args.beta, max_prompt_length=args.max_prompt, max_completion_length=args.max_completion,
                    max_length=args.max_prompt + args.max_completion, truncation_mode="keep_end", **common)
    trainer = DPOTrainer(model=model, args=cfg, train_dataset=ds, processing_class=tok, peft_config=peft_cfg)
else:
    from trl import SFTConfig, SFTTrainer
    ds = Dataset.from_list([{"prompt": r["prompt"], "completion": r["completion"] + tok.eos_token} for r in rows])
    cfg = SFTConfig(max_length=args.max_prompt + args.max_completion, completion_only_loss=True, **common)
    trainer = SFTTrainer(model=model, args=cfg, train_dataset=ds, processing_class=tok, peft_config=peft_cfg)

trainer.train()
trainer.model.save_pretrained(args.out)
tok.save_pretrained(args.out)
json.dump({"log": trainer.state.log_history, "args": vars(args), "n": len(rows)}, open(f"{args.out}/train_log.json", "w"), indent=1)
print("saved", args.out)
