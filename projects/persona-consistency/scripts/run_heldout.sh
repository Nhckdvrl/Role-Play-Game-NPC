#!/bin/bash
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; H=~/rp_persona/data/e0c_probes_heldout.jsonl
$PY gen_heldout_probes.py > $R/heldout_probes.log 2>&1 || { echo "probe gen failed"; exit 1; }
cat $R/heldout_probes.log | grep wrote
PT=false_q,meta_p1,meta_p2,meta_p3
$PY e0d_mechanism.py --probes $H --policy_url http://localhost:8010/v1 --policy_name q8 --policy_label base --depth 20 --conds full --n 4 --probe_types $PT --out $R/e1/heldout_base_d20.jsonl > $R/heldout_base.log 2>&1 &
$PY e0d_mechanism.py --probes $H --policy_url http://localhost:8010/v1 --policy_name impall2 --policy_label impall2 --depth 20 --conds full --n 4 --probe_types $PT --out $R/e1/heldout_impall2_d20.jsonl > $R/heldout_impall2.log 2>&1 &
$PY e0d_mechanism.py --probes $H --policy_url http://localhost:8007/v1 --policy_name r2 --policy_tok /tmp/xiang_rp/models/Qwen3-8B-r1 --policy_label r2 --depth 20 --conds full --n 4 --probe_types $PT --out $R/e1/heldout_r2_d20.jsonl > $R/heldout_r2.log 2>&1 &
wait
echo "heldout gen done $(date)"
$PY e0c_judge.py --probes $H --inp $R/e1/heldout_base_d20.jsonl $R/e1/heldout_impall2_d20.jsonl $R/e1/heldout_r2_d20.jsonl > $R/heldout_judge.log 2>&1
echo "HELDOUT DONE $(date)"
