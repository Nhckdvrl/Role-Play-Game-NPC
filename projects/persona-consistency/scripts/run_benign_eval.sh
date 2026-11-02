#!/bin/bash
# Over-guardedness eval: benign questions at depth 20 for base, implicit-all (GPU1 server) and r2 (merged, served by the round-3 chain).
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; H=~/rp_persona/data/e0c_probes_heldout.jsonl
until grep -q "r2m up" $R/chain_e1v5.log; do sleep 30; done
$PY add_benign_probes.py > $R/benign_probes.log 2>&1
until ! nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 1 | grep -q .; do sleep 20; done
TP=1 nohup ~/rp_persona/scripts/serve_lora.sh 1 8013 impall2=/tmp/xiang_rp/e1v2/impall > $R/serve_benign.log 2>&1 &
until curl -s http://localhost:8013/v1/models | grep -q impall2; do sleep 10; done
$PY e0d_mechanism.py --probes $H --policy_url http://localhost:8013/v1 --policy_name q8 --policy_label base --depth 20 --conds full --n 4 --probe_types benign_q --out $R/e1/benign_base_d20.jsonl > $R/benign_base.log 2>&1 &
P1=$!
$PY e0d_mechanism.py --probes $H --policy_url http://localhost:8013/v1 --policy_name impall2 --policy_label impall2 --depth 20 --conds full --n 4 --probe_types benign_q --out $R/e1/benign_impall2_d20.jsonl > $R/benign_impall2.log 2>&1 &
P2=$!
$PY e0d_mechanism.py --probes $H --policy_url http://localhost:8011/v1 --policy_name q8r2 --policy_tok /tmp/xiang_rp/models/Qwen3-8B-r2 --policy_label r2 --depth 20 --conds full --n 4 --probe_types benign_q --out $R/e1/benign_r2_d20.jsonl > $R/benign_r2.log 2>&1 &
P3=$!
wait $P1 $P2 $P3
$PY e0c_judge.py --probes $H --inp $R/e1/benign_base_d20.jsonl $R/e1/benign_impall2_d20.jsonl $R/e1/benign_r2_d20.jsonl > $R/benign_judge.log 2>&1
echo "BENIGN DONE $(date)"
