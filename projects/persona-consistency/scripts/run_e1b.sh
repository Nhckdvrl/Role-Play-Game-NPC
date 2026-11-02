#!/bin/bash
# E1b distillation data: generation on GPU0 (released as soon as generation finishes), judging on Qwen3-32B.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
rm -f ~/rp_persona/runs/e1b_gen_done
nohup ~/rp_persona/scripts/serve.sh /tmp/xiang_rp/models/Qwen3-8B 0 1 8005 q8 > ~/rp_persona/runs/serve_q8_e1b.log 2>&1 &
SP=$!
until curl -s http://localhost:8005/v1/models | grep -q q8; do sleep 10; done
$PY e1b_distill_data.py --policy_url http://localhost:8005/v1 > ~/rp_persona/runs/e1b_data.log 2>&1 &
DP=$!
until [ -f ~/rp_persona/runs/e1b_gen_done ] || ! kill -0 $DP 2>/dev/null; do sleep 10; done
kill $SP; sleep 10
for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 0); do kill $p; done
echo "gen done, GPU0 released $(date)"
wait $DP
echo "E1B DATA DONE $(date)"
