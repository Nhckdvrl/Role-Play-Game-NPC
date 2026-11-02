#!/bin/bash
# Waits for the local Qwen3-32B copy, then: holistic judge on E0-A -> E0-B rewrites -> E0-B rollouts (8B on GPU0).
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
until grep -q COPY_DONE /tmp/xiang_rp/copy.log; do sleep 15; done
echo "copy done $(date)"
CUDA_VISIBLE_DEVICES=2,3 $PY rewrite_mt.py --model /tmp/xiang_rp/models/Qwen3-32B > ~/rp_persona/runs/e0b_rewrite.log 2>&1
echo "rewrite done $(date)"
CUDA_VISIBLE_DEVICES=0 nohup $PY rollout_mt.py --model /tmp/xiang_rp/models/Qwen3-8B --tag q8 > ~/rp_persona/runs/e0b_roll_q8.log 2>&1 &
CUDA_VISIBLE_DEVICES=2,3 $PY judge_holistic.py --model /tmp/xiang_rp/models/Qwen3-32B --gen ~/rp_persona/runs/e0a/gen_q8.jsonl > ~/rp_persona/runs/e0a_judge_q8.log 2>&1
echo "judge done $(date)"
wait
echo "rollout done $(date)"
CUDA_VISIBLE_DEVICES=2,3 $PY judge_mt.py --model /tmp/xiang_rp/models/Qwen3-32B --roll ~/rp_persona/runs/e0b/roll_q8.jsonl > ~/rp_persona/runs/e0b_judge_q8.log 2>&1
echo "ALL DONE $(date)"
