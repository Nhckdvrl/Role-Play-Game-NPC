"""Shared helpers for the mechanism experiments (plain transformers + PyTorch hooks)."""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def load(model_dir, device="cuda:0"):
    kw = {"fix_mistral_regex": True} if "mistral" in model_dir.lower() else {}
    tok = AutoTokenizer.from_pretrained(model_dir, **kw)
    model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=torch.bfloat16, device_map=device)
    import os
    if os.environ.get("LORA"):
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, os.environ["LORA"]).merge_and_unload()
    model.eval()
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    return tok, model


def layers_of(model):
    m = model
    for path in ("model.language_model.layers", "model.layers", "language_model.model.layers"):
        obj = m
        try:
            for p in path.split("."):
                obj = getattr(obj, p)
            return obj
        except AttributeError:
            continue
    raise RuntimeError("cannot find decoder layers")


def render(tok, messages, tag):
    kw = {"enable_thinking": False} if "qwen3" in tag.lower() else {}
    return tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, **kw)


def letter_ids(tok):
    ids = {}
    for L in ("A", "B"):
        e = tok.encode(L, add_special_tokens=False)
        assert len(e) == 1, (L, e)
        ids[L] = e[0]
    return ids
