#!/bin/bash
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
until grep -q "impall trained" ~/rp_persona/runs/train_impall.log; do sleep 30; done
CUDA_VISIBLE_DEVICES=1 $PY e0g2_feats.py > ~/rp_persona/runs/e0g2_feats.log 2>&1 && $PY analyze_e0g2.py --out results/e0g2_minimalpair_q8.txt > ~/rp_persona/runs/e0g2_analysis.log 2>&1
echo "E0G2 DONE $(date)"
