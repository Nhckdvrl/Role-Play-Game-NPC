#!/bin/bash
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs
until grep -q "rep2 gen done" $R/closedloop_rep2.log; do sleep 30; done
for p in $(pgrep -f "[l]ora-modules impall2=/tmp/xiang_rp/e1v2/impall"); do kill $p; done; sleep 15
for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 1); do kill $p; done; sleep 5
CUDA_VISIBLE_DEVICES=1 $PY e0j_attention.py --out $R/e0g/attn_base.json > $R/e0j_base.log 2>&1
CUDA_VISIBLE_DEVICES=1 $PY e0j_attention.py --adapter /tmp/xiang_rp/e1v2/impall --out $R/e0g/attn_impall2.json > $R/e0j_impall2.log 2>&1
echo "E0J DONE $(date)"
