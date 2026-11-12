"""LoRA SFT on DEV decision data (build_sft.py output). Loss on the assistant answer letter only.

usage: train_sft.py MODEL_DIR TAG SFT.jsonl OUT_DIR [epochs=1]
"""
import json
import sys

import torch
from datasets import Dataset
from peft import LoraConfig
from transformers import AutoTokenizer
from trl import SFTConfig, SFTTrainer

model_dir, tag, data, out = sys.argv[1:5]
epochs = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
tok = AutoTokenizer.from_pretrained(model_dir)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
rows = [json.loads(l) for l in open(data)]
kw = {"enable_thinking": False} if "qwen3" in tag else {}


def to_pc(r):
    prompt = tok.apply_chat_template(r["messages"][:-1], tokenize=False, add_generation_prompt=True, **kw)
    return {"prompt": prompt, "completion": r["messages"][-1]["content"]}


ds = Dataset.from_list([to_pc(r) for r in rows])
cfg = SFTConfig(output_dir=out, num_train_epochs=epochs, per_device_train_batch_size=4, gradient_accumulation_steps=4,
                learning_rate=1e-4, lr_scheduler_type="cosine", warmup_ratio=0.03, logging_steps=20, save_strategy="no",
                bf16=True, max_length=2048, completion_only_loss=True, report_to=[], gradient_checkpointing=True,
                model_init_kwargs={"dtype": torch.bfloat16})
peft_cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                      task_type="CAUSAL_LM")
trainer = SFTTrainer(model=model_dir, args=cfg, train_dataset=ds, processing_class=tok, peft_config=peft_cfg)
trainer.train()
trainer.model.save_pretrained(out)
tok.save_pretrained(out)
print("saved", out)
