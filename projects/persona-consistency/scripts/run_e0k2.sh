#!/bin/bash
# E0-K v2: single-layer injection of the training-derived difference (L16 or L23), scale 1; two runs in parallel on GPU1.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; export PYTHONHASHSEED=0
for L in 16 23; do
  CUDA_VISIBLE_DEVICES=1 $PY e0k_transfer_steer.py --layers $L --conds none,transfer --probe_types false_premise,meta_ai \
    --out $R/e0i/transfer_L${L}_d20.jsonl > $R/e0k2_L$L.log 2>&1 &
done
wait
sed 's/"policy": "steer:transfer"/"policy": "steer:transfer_L16"/; s/"policy": "steer:none"/"policy": "steer:none_a"/' $R/e0i/transfer_L16_d20.jsonl > $R/e0i/transfer_single.jsonl
sed 's/"policy": "steer:transfer"/"policy": "steer:transfer_L23"/; s/"policy": "steer:none"/"policy": "steer:none_b"/' $R/e0i/transfer_L23_d20.jsonl >> $R/e0i/transfer_single.jsonl
$PY e0c_judge.py --inp $R/e0i/transfer_single.jsonl > $R/e0k2_judge.log 2>&1
echo "E0K2 DONE $(date)"
