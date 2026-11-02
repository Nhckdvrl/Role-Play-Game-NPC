#!/bin/bash
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
until curl -s http://localhost:8003/v1/models | grep -q q8; do sleep 10; done
echo "q8b up $(date)"
$PY e1_data.py --policy_url http://localhost:8003/v1 --n_convs 128 --k_def 5 --k_sc 3 > ~/rp_persona/runs/e1_data.log 2>&1 || { echo "e1 data failed"; exit 1; }
echo "ALL DONE $(date)"
