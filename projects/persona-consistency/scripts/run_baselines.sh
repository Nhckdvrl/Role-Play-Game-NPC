#!/bin/bash
# Supplementary depth-20 baselines on GPU0 while implicit_all_v2 trains on GPU1: base / selfcheck_sys / reanchor, 8 fresh samples.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
until grep -q "rft_v2 trained" ~/rp_persona/runs/chain_e1v2.log; do sleep 30; done
nohup ~/rp_persona/scripts/serve.sh /tmp/xiang_rp/models/Qwen3-8B 0 1 8005 q8 > ~/rp_persona/runs/serve_q8_base.log 2>&1 &
SP=$!
until curl -s http://localhost:8005/v1/models | grep -q q8; do sleep 10; done
$PY e0d_mechanism.py --policy_url http://localhost:8005/v1 --policy_label base --depth 20 --conds full,selfcheck_sys,reanchor \
  --probe_types false_premise,meta_ai,true_premise,none --n 8 --sample_offset 100 --out ~/rp_persona/runs/e1/base_supp_d20.jsonl > ~/rp_persona/runs/base_supp.log 2>&1
echo "baseline gen done $(date)"
kill $SP; sleep 10
for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 0); do kill $p; done
$PY e0c_judge.py --inp ~/rp_persona/runs/e1/base_supp_d20.jsonl > ~/rp_persona/runs/base_supp_judge.log 2>&1
echo "BASELINES DONE $(date)"
