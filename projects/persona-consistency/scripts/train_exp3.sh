#!/bin/bash
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
until grep -qE "v2 eval gen done|failed" ~/rp_persona/runs/chain_e1v2.log; do sleep 20; done
sleep 40   # let after_v2gen.sh release GPUs 0,1
CUDA_VISIBLE_DEVICES=1 $PY e1_train.py --algo dpo --data ~/rp_persona/data/e1_v3/dpo_explicit.jsonl --out /tmp/xiang_rp/e1v3/exp > ~/rp_persona/runs/e1v3_train_exp.log 2>&1
echo "exp_v3 trained $(date)"
