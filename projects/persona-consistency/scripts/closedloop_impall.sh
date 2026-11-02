#!/bin/bash
# Closed-loop E0-C protocol for the implicit-all adapter (it generates its own 20-turn histories).
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
until grep -qE "v3 eval gen done|failed" ~/rp_persona/runs/chain_e1v3.log; do sleep 30; done
$PY e0c_stress.py --tag impall2_her --mode her --policy_url http://localhost:8001/v1 --policy_name impall2 \
  --policy_tok /tmp/xiang_rp/models/Qwen3-8B --sim_url http://localhost:8000/v1 > ~/rp_persona/runs/e0c_impall2.log 2>&1 || { echo "closed loop failed"; exit 1; }
echo "closed-loop gen done $(date)"
until grep -qE "ALL DONE|failed" ~/rp_persona/runs/chain_e1v3.log; do sleep 30; done
$PY e0c_judge.py --probes ~/rp_persona/data/e0c_probes_v1.jsonl --inp ~/rp_persona/runs/e0c/e0c_impall2_her.jsonl > ~/rp_persona/runs/e0c_judge_impall2.log 2>&1
echo "CLOSED LOOP DONE $(date)"
