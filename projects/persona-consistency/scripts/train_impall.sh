#!/bin/bash
# Train dpo_implicit_all (358 pairs, lr 5e-5) on GPU1 once E0-G feature extraction has released it.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
until grep -qE "sft \+ feats done|failed" ~/rp_persona/runs/chain_e1.log; do sleep 20; done
CUDA_VISIBLE_DEVICES=1 $PY e1_train.py --algo dpo --lr 5e-5 --data ~/rp_persona/data/e1_all/dpo_implicit_all.jsonl \
  --out /tmp/xiang_rp/e1/dpo_implicit_all > ~/rp_persona/runs/e1_train_impall.log 2>&1
echo "impall trained $(date)"
