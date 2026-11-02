#!/bin/bash
# Rerun E0-B plain mode with fixed format stripping; re-judge both modes with the fixed judge setup.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
CUDA_VISIBLE_DEVICES=0 $PY rollout_mt.py --model /tmp/xiang_rp/models/Qwen3-8B --tag q8plain --mode plain > ~/rp_persona/runs/e0b_roll_q8plain.log 2>&1 &
CUDA_VISIBLE_DEVICES=2,3 $PY judge_mt.py --model /tmp/xiang_rp/models/Qwen3-32B --roll ~/rp_persona/runs/e0b/roll_q8.jsonl > ~/rp_persona/runs/e0b_judge_q8.log 2>&1
wait
CUDA_VISIBLE_DEVICES=2,3 $PY judge_mt.py --model /tmp/xiang_rp/models/Qwen3-32B --roll ~/rp_persona/runs/e0b/roll_q8plain.jsonl > ~/rp_persona/runs/e0b_judge_q8plain.log 2>&1
echo "ALL DONE $(date)"
