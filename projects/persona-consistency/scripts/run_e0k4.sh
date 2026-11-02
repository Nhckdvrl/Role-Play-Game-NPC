#!/bin/bash
# E0-K v4: side effects of the L16 x2 training-derived vector on true-premise and natural turns (same seeds convention).
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; export PYTHONHASHSEED=0
CUDA_VISIBLE_DEVICES=1 $PY e0k_transfer_steer.py --layers 16 --scale 2 --conds none,transfer --probe_types true_premise,none \
  --probes ~/rp_persona/data/e0c_probes_v2_validated.jsonl --out $R/e0i/transfer_L16x2_side.jsonl > $R/e0k4.log 2>&1
$PY e0c_judge.py --inp $R/e0i/transfer_L16x2_side.jsonl > $R/e0k4_judge.log 2>&1
echo "E0K4 DONE $(date)"
