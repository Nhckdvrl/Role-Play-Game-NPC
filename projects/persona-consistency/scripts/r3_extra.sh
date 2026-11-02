#!/bin/bash
# r3 checks for the side effects it was designed to fix: benign-question evasiveness (multi-turn) and single-turn APC fact use.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; H=~/rp_persona/data/e0c_probes_heldout.jsonl; M=/tmp/xiang_rp/models
until grep -qE "ALL DONE|failed" $R/chain_e1v5b.log; do sleep 60; done
$PY e0d_mechanism.py --probes $H --policy_url http://localhost:8012/v1 --policy_name r3 --policy_tok $M/Qwen3-8B-r2 --policy_label r3 \
  --depth 20 --conds full --n 4 --probe_types benign_q --out $R/e1/benign_r3_d20.jsonl > $R/benign_r3.log 2>&1
$PY gen_apc_server.py --url http://localhost:8012/v1 --models r3 --tok $M/Qwen3-8B-r2 > $R/apc_r3_gen.log 2>&1
$PY e0c_judge.py --probes $H --inp $R/e1/benign_r3_d20.jsonl > $R/benign_r3_judge.log 2>&1
until ! nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 1 | grep -q .; do sleep 30; done
CUDA_VISIBLE_DEVICES=1 $PY score_apc.py --gen $R/e0a/gen_srv_r3.jsonl > $R/apc_r3_score.log 2>&1
echo "R3 EXTRA DONE $(date)"
