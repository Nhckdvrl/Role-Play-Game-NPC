#!/bin/bash
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; export PYTHONHASHSEED=0
until ! nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 1 | grep -q .; do sleep 20; done
CUDA_VISIBLE_DEVICES=1 $PY e0k_transfer_steer.py --probe_types false_premise,meta_ai --out $R/e0i/transfer_d20.jsonl > $R/e0k.log 2>&1
$PY e0c_judge.py --inp $R/e0i/transfer_d20.jsonl > $R/e0k_judge.log 2>&1
echo "E0K DONE $(date)"
