"""Merge a LoRA adapter into its base model and save a standalone checkpoint (next-round policy / DPO reference)."""
import argparse, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

ap = argparse.ArgumentParser()
ap.add_argument("--base", default="/tmp/xiang_rp/models/Qwen3-8B")
ap.add_argument("--adapter", required=True)
ap.add_argument("--out", required=True)
args = ap.parse_args()

model = AutoModelForCausalLM.from_pretrained(args.base, torch_dtype=torch.bfloat16)
model = PeftModel.from_pretrained(model, args.adapter).merge_and_unload()
model.save_pretrained(args.out, safe_serialization=True)
AutoTokenizer.from_pretrained(args.base).save_pretrained(args.out)
print("merged ->", args.out)
