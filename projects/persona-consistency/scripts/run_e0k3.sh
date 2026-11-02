#!/bin/bash
# E0-K v3: L16 at 2x and L20 at 1x (single-layer injection), parallel on GPU1; same seeds as v2.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; export PYTHONHASHSEED=0
CUDA_VISIBLE_DEVICES=1 $PY e0k_transfer_steer.py --layers 16 --scale 2 --conds none,transfer --probe_types false_premise,meta_ai --out $R/e0i/transfer_L16x2_d20.jsonl > $R/e0k3_L16x2.log 2>&1 &
CUDA_VISIBLE_DEVICES=1 $PY e0k_transfer_steer.py --layers 20 --scale 1 --conds none,transfer --probe_types false_premise,meta_ai --out $R/e0i/transfer_L20_d20.jsonl > $R/e0k3_L20.log 2>&1 &
wait
sed 's/"policy": "steer:transfer"/"policy": "steer:transfer_L16x2"/; s/"policy": "steer:none"/"policy": "steer:none_c"/' $R/e0i/transfer_L16x2_d20.jsonl > $R/e0i/transfer_v3.jsonl
sed 's/"policy": "steer:transfer"/"policy": "steer:transfer_L20"/; s/"policy": "steer:none"/"policy": "steer:none_d"/' $R/e0i/transfer_L20_d20.jsonl >> $R/e0i/transfer_v3.jsonl
until curl -s http://localhost:8000/v1/models | grep -q q32; do sleep 30; done
$PY e0c_judge.py --inp $R/e0i/transfer_v3.jsonl > $R/e0k3_judge.log 2>&1
echo "E0K3 DONE $(date)"
