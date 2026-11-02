#!/bin/bash
# Cross-judge E1 v2 key files with Mistral while Qwen3-32B is idle; restore Qwen3-32B afterwards.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs
M=$(ls -d ~/.cache/huggingface/hub/models--mistralai--Mistral-Small-24B-Instruct-2501/snapshots/*/)
until grep -q "E1B DATA DONE" $R/run_e1b.log; do sleep 20; done
for p in $(pgrep -f "[a]pi_server --model /tmp/xiang_rp/models/Qwen3-32B"); do kill $p; done; sleep 20
nohup ~/rp_persona/scripts/serve.sh $M 2,3 2 8004 mistral > $R/serve_mistral.log 2>&1 &
until curl -s http://localhost:8004/v1/models | grep -q mistral; do sleep 15; done
echo "mistral up $(date)"
$PY e0c_judge.py --url http://localhost:8004/v1 --name mistral --tok $M --out_suffix .judge_mistral.jsonl \
  --inp $R/e1/eval_q8_d20.jsonl $R/e1/evalv2_impall2_d20.jsonl $R/e1/evalv2_imp2_d20.jsonl $R/e1/base_supp_d20.jsonl > $R/xjudge_v2.log 2>&1
echo "xjudge done $(date)"
for p in $(pgrep -f "[a]pi_server --model $M"); do kill $p; done; sleep 20
nohup ~/rp_persona/scripts/serve.sh /tmp/xiang_rp/models/Qwen3-32B 2,3 2 8000 q32 > $R/serve_q32.log 2>&1 &
until curl -s http://localhost:8000/v1/models | grep -q q32; do sleep 10; done
echo "q32 restored $(date)"
