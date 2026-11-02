#!/bin/bash
# Protect the E1 v2 eval: when implicit_all_v2 finishes, stop E1b generation if it still holds GPU0.
until grep -q "impall_v2 trained" ~/rp_persona/runs/chain_e1v2.log; do sleep 10; done
if [ ! -f ~/rp_persona/runs/e1b_gen_done ]; then
  for p in $(pgrep -f "[r]un_e1b.sh") $(pgrep -f "[e]1b_distill_data.py") $(pgrep -f "[s]erved-model-name q8 --tensor-parallel-size 1 --port 8005"); do kill $p; done
  sleep 10
  for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 0); do kill $p; done
  echo "E1B STOPPED for v2 eval $(date)"
else
  echo "e1b gen had finished $(date)"
fi
