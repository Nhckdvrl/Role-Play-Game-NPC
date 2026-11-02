#!/bin/bash
# Mechanistic link: do trained adapters move depth-20 states back toward the base model's anchor direction?
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
until grep -q "E0I DONE\|steer gen done" ~/rp_persona/runs/run_e0i.log; do sleep 30; done
G=~/rp_persona/runs/e0g
CUDA_VISIBLE_DEVICES=0 $PY e0h_anchor.py --save_dirs $G/anchor_dirs_base.npy --out $G/anchor_q8_rerun.json > $G/../e0h_base_rerun.log 2>&1
for A in impall2:/tmp/xiang_rp/e1v2/impall ddpo:/tmp/xiang_rp/e1v3/ddpo imp5:/tmp/xiang_rp/e1v3/imp5; do
  N=${A%%:*}; P=${A#*:}
  CUDA_VISIBLE_DEVICES=0 $PY e0h_anchor.py --adapter $P --load_dirs $G/anchor_dirs_base.npy --out $G/anchor_$N.json > $G/../e0h_$N.log 2>&1
done
echo "ANCHOR LINK DONE $(date)"
