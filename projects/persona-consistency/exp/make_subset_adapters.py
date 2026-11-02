"""Layer-subset ablation of a LoRA adapter: keep the update only in a layer range (zero lora_B elsewhere)."""
import argparse, os, re, shutil
from safetensors.torch import load_file, save_file

ap = argparse.ArgumentParser()
ap.add_argument("--adapter", required=True)
ap.add_argument("--subsets", default="early:0-11,mid:12-23,late:24-35")
args = ap.parse_args()
sd = load_file(os.path.join(args.adapter, "adapter_model.safetensors"))
for spec in args.subsets.split(","):
    name, rng = spec.split(":")
    lo, hi = map(int, rng.split("-"))
    out = {}
    for k, v in sd.items():
        m = re.search(r"layers\.(\d+)\.", k)
        keep = m and lo <= int(m.group(1)) <= hi
        out[k] = v if ("lora_A" in k or keep) else v * 0
    dst = args.adapter.rstrip("/") + f"_{name}"
    os.makedirs(dst, exist_ok=True)
    save_file(out, os.path.join(dst, "adapter_model.safetensors"))
    shutil.copy(os.path.join(args.adapter, "adapter_config.json"), dst)
    print("wrote", dst)
