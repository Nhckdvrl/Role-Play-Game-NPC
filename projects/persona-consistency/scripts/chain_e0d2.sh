#!/bin/bash
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
$PY e0c_judge.py --inp ~/rp_persona/runs/e0c/e0c_her32.jsonl > ~/rp_persona/runs/e0c_judge_her32.log 2>&1 &
$PY e0c_stress.py --tag her32_d20 --mode her --depths 20 --max_tokens 2048 --policy_url http://localhost:8002/v1 --policy_name her32 \
  --policy_tok /tmp/xiang_rp/models/HER-32B --policy_no_think_flag > ~/rp_persona/runs/e0c_her32_d20.log 2>&1
echo "her32_d20 gen exit $? $(date)"
pkill -f "served-model-name her32"; sleep 15
for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 0,1); do kill $p; done; sleep 5
nohup ~/rp_persona/scripts/serve.sh /tmp/xiang_rp/models/Qwen3-8B 0 1 8001 q8 > ~/rp_persona/runs/serve_q8.log 2>&1 &
until curl -s http://localhost:8001/v1/models | grep -q q8; do sleep 10; done
echo "q8 up $(date)"
$PY e0c_judge.py --inp ~/rp_persona/runs/e0c/e0c_her32_d20.jsonl > ~/rp_persona/runs/e0c_judge_her32_d20.log 2>&1 &
$PY e0d_mechanism.py --depth 20 --out ~/rp_persona/runs/e0d/e0d_q8her_d20.jsonl > ~/rp_persona/runs/e0d_d20.log 2>&1
$PY e0d_mechanism.py --depth 2 --conds full --out ~/rp_persona/runs/e0d/e0d_q8her_d2.jsonl > ~/rp_persona/runs/e0d_d2.log 2>&1
echo "e0d gen done $(date)"
wait
$PY e0c_judge.py --inp ~/rp_persona/runs/e0d/e0d_q8her_d20.jsonl ~/rp_persona/runs/e0d/e0d_q8her_d2.jsonl > ~/rp_persona/runs/e0d_judge.log 2>&1
echo "ALL DONE $(date)"
