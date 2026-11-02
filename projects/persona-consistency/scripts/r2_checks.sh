#!/bin/bash
# r2 robustness: (a) APC single-turn regression via the r2 server; (b) Mistral cross-judge of r2 closed loop, fixed-history and held-out evals.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs
M=$(ls -d ~/.cache/huggingface/hub/models--mistralai--Mistral-Small-24B-Instruct-2501/snapshots/*/)
(
  $PY gen_apc_server.py --url http://localhost:8007/v1 --models r2 --tok /tmp/xiang_rp/models/Qwen3-8B-r1 > $R/apc_r2_gen.log 2>&1
  for p in $(pgrep -f "[s]erved-model-name q8 --port 8010"); do kill $p; done; sleep 15
  for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 1); do kill $p; done; sleep 5
  CUDA_VISIBLE_DEVICES=1 $PY score_apc.py --gen $R/e0a/gen_srv_r2.jsonl > $R/apc_r2_score.log 2>&1
  echo "apc r2 done $(date)"
) &
AP=$!
for p in $(pgrep -f "[a]pi_server --model /tmp/xiang_rp/models/Qwen3-32B"); do kill $p; done; sleep 20
nohup ~/rp_persona/scripts/serve.sh $M 2,3 2 8004 mistral > $R/serve_mistral.log 2>&1 &
until curl -s http://localhost:8004/v1/models | grep -q mistral; do sleep 15; done
$PY e0c_judge.py --url http://localhost:8004/v1 --name mistral --tok $M --out_suffix .judge_mistral.jsonl \
  --probes ~/rp_persona/data/e0c_probes_v1.jsonl --inp $R/e0c/e0c_r2_her.jsonl > $R/xjudge_r2.log 2>&1
$PY e0c_judge.py --url http://localhost:8004/v1 --name mistral --tok $M --out_suffix .judge_mistral.jsonl \
  --inp $R/e1/evalv4_r2_d20.jsonl >> $R/xjudge_r2.log 2>&1
$PY e0c_judge.py --url http://localhost:8004/v1 --name mistral --tok $M --out_suffix .judge_mistral.jsonl \
  --probes ~/rp_persona/data/e0c_probes_heldout.jsonl --inp $R/e1/heldout_base_d20.jsonl $R/e1/heldout_impall2_d20.jsonl $R/e1/heldout_r2_d20.jsonl >> $R/xjudge_r2.log 2>&1
echo "xjudge r2 done $(date)"
for p in $(pgrep -f "[a]pi_server --model $M"); do kill $p; done; sleep 20
nohup ~/rp_persona/scripts/serve.sh /tmp/xiang_rp/models/Qwen3-32B 2,3 2 8000 q32 > $R/serve_q32.log 2>&1 &
until curl -s http://localhost:8000/v1/models | grep -q q32; do sleep 10; done
wait $AP
echo "R2 CHECKS DONE $(date)"
