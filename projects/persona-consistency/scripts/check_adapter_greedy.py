import json, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
M = "/tmp/xiang_rp/models/Qwen3-8B"
tok = AutoTokenizer.from_pretrained(M)
model = AutoModelForCausalLM.from_pretrained(M, torch_dtype=torch.bfloat16, device_map="cuda")
model = PeftModel.from_pretrained(model, "/tmp/xiang_rp/e1v3/exp").eval()
rows = [json.loads(l) for l in open("/home/xiang/rp_persona/data/e1_v3/dpo_explicit.jsonl")][:3]
for r in rows:
    ids = tok(r["prompt"], return_tensors="pt", add_special_tokens=False).input_ids.cuda()
    with torch.no_grad():
        out = model.generate(ids, max_new_tokens=30, do_sample=False)
        logits = model(ids).logits[0, -1].float().log_softmax(-1)
    top = torch.topk(logits, 5)
    print(repr(tok.decode(out[0, ids.shape[1]:])), {tok.decode([i]): round(v.item(), 2) for v, i in zip(top.values, top.indices)})
