#!/bin/bash
# Regression check on the single-turn APC set: base vs implicit-all (fact use, length, format).
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs
until grep -q "E0J DONE" $R/run_e0j.log; do sleep 30; done
TP=1 nohup ~/rp_persona/scripts/serve_lora.sh 1 8009 impall2=/tmp/xiang_rp/e1v2/impall > $R/serve_apc.log 2>&1 &
SP=$!
until curl -s http://localhost:8009/v1/models | grep -q impall2; do sleep 10; done
$PY gen_apc_server.py --url http://localhost:8009/v1 --models q8,impall2 > $R/apc_regress_gen.log 2>&1
kill $SP; sleep 15; for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 1); do kill $p; done; sleep 5
CUDA_VISIBLE_DEVICES=1 $PY score_apc.py --gen $R/e0a/gen_srv_q8.jsonl $R/e0a/gen_srv_impall2.jsonl > $R/apc_regress_score.log 2>&1
echo "APC REGRESS DONE $(date)"
