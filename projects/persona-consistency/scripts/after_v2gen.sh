#!/bin/bash
# After E1 v2 eval generation: release the LoRA server and rerun E1b distillation data (judging shares Qwen3-32B).
until grep -qE "v2 eval gen done|failed" ~/rp_persona/runs/chain_e1v2.log; do sleep 20; done
for p in $(pgrep -f "[l]ora-modules imp2="); do kill $p; done; sleep 15
for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 0,1); do kill $p; done; sleep 5
~/rp_persona/scripts/run_e1b.sh > ~/rp_persona/runs/run_e1b.log 2>&1
