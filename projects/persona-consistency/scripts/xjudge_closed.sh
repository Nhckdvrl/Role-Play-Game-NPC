#!/bin/bash
# Mistral cross-judge of the closed-loop runs (impall2, ddpo); base E0-C q8her already has Mistral labels.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs
M=$(ls -d ~/.cache/huggingface/hub/models--mistralai--Mistral-Small-24B-Instruct-2501/snapshots/*/)
for p in $(pgrep -f "[a]pi_server --model /tmp/xiang_rp/models/Qwen3-32B"); do kill $p; done; sleep 20
nohup ~/rp_persona/scripts/serve.sh $M 2,3 2 8004 mistral > $R/serve_mistral.log 2>&1 &
until curl -s http://localhost:8004/v1/models | grep -q mistral; do sleep 15; done
$PY e0c_judge.py --url http://localhost:8004/v1 --name mistral --tok $M --out_suffix .judge_mistral.jsonl \
  --probes ~/rp_persona/data/e0c_probes_v1.jsonl --inp $R/e0c/e0c_impall2_her.jsonl $R/e0c/e0c_ddpo_her.jsonl > $R/xjudge_closed.log 2>&1
echo "xjudge closed done $(date)"
for p in $(pgrep -f "[a]pi_server --model $M"); do kill $p; done; sleep 20
nohup ~/rp_persona/scripts/serve.sh /tmp/xiang_rp/models/Qwen3-32B 2,3 2 8000 q32 > $R/serve_q32.log 2>&1 &
until curl -s http://localhost:8000/v1/models | grep -q q32; do sleep 10; done
echo "q32 restored $(date)"
