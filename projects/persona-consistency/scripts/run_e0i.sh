#!/bin/bash
# E0-I after the closed-loop run releases GPUs 0,1: two steering shards, then judge on Qwen3-32B.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
until grep -qE "closed-loop gen done|closed loop failed" ~/rp_persona/runs/closedloop_impall.log && grep -qE "closed-loop gen done|closed loop failed" ~/rp_persona/runs/closedloop_ddpo.log; do sleep 30; done
for p in $(pgrep -f "[l]ora-modules impall2="); do kill $p; done; sleep 20
for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 0,1); do kill $p; done; sleep 5
for S in 0 1; do
  CUDA_VISIBLE_DEVICES=$S $PY e0i_steer.py --shard $S/2 --out ~/rp_persona/runs/e0i/steer_s$S.jsonl > ~/rp_persona/runs/e0i_s$S.log 2>&1 &
done
wait
cat ~/rp_persona/runs/e0i/steer_s0.jsonl ~/rp_persona/runs/e0i/steer_s1.jsonl > ~/rp_persona/runs/e0i/steer_d20.jsonl
echo "steer gen done $(date)"
until grep -qE "CLOSED LOOP DONE" ~/rp_persona/runs/closedloop_impall.log && grep -qE "CLOSED LOOP DONE" ~/rp_persona/runs/closedloop_ddpo.log; do sleep 30; done
$PY e0c_judge.py --inp ~/rp_persona/runs/e0i/steer_d20.jsonl > ~/rp_persona/runs/e0i_judge.log 2>&1
echo "E0I DONE $(date)"
