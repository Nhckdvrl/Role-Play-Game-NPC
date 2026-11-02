"""Where did the adapters change the model? Frobenius norm of each LoRA update dW = (alpha/r) * B @ A, per layer and module."""
import json, re, sys, collections
import torch
from safetensors.torch import load_file

for name in sys.argv[1:]:
    sd = load_file(f"/home/xiang/rp_persona/runs/e0g/lora_{name}.safetensors")
    cfg = json.load(open(f"/home/xiang/rp_persona/runs/e0g/lora_{name}_config.json"))
    scale = cfg["lora_alpha"] / cfg["r"]
    norms = collections.defaultdict(dict)
    for k in sd:
        if "lora_A" not in k:
            continue
        m = re.search(r"layers\.(\d+)\.(self_attn|mlp)\.(\w+)\.lora_A", k)
        A, B = sd[k].float(), sd[k.replace("lora_A", "lora_B")].float()
        norms[int(m.group(1))][m.group(3)] = (scale * (B @ A)).norm().item()
    layers = sorted(norms)
    mods = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    tot = {l: sum(norms[l].values()) for l in layers}
    print(f"== {name}: total update norm per layer (bar) and share by module group")
    mx = max(tot.values())
    for l in layers:
        attn = sum(norms[l][m] for m in mods[:4]); mlp = sum(norms[l][m] for m in mods[4:])
        print(f"L{l:2d} {tot[l]:6.3f} {'#' * int(40 * tot[l] / mx):40s} attn {attn / tot[l]:.2f} | mlp {mlp / tot[l]:.2f}")
    thirds = [sum(tot[l] for l in layers if lo <= l < hi) for lo, hi in ((0, 12), (12, 24), (24, 36))]
    print("share by depth third (0-11 / 12-23 / 24-35):", " / ".join(f"{t / sum(thirds):.2f}" for t in thirds))
    print("module totals:", {m: round(sum(norms[l][m] for l in layers), 3) for m in mods})
