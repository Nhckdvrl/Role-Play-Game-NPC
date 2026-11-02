#!/bin/bash
# start E0-L (Assistant Axis) on GPU1 once r2'' training is done (GPU1 is idle during the r2'' eval phase)
until grep -q "r2pp server up" ~/rp_persona/runs/chain_r2pp_b.log; do sleep 60; done
cd /home/xiang/Role-Play-Game-NPC/exp
CUDA_VISIBLE_DEVICES=1 ~/miniconda3/envs/verl-clean/bin/python e0l_assistant_axis.py > ~/rp_persona/runs/e0l.log 2>&1
echo "P3 DONE $(date)" >> ~/rp_persona/runs/e0l.log
