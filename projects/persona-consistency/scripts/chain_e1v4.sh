#!/bin/bash
# E1 v4: round-2 on-policy DPO from the merged implicit-all policy (r1), closed-loop data and evaluation.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; M=/tmp/xiang_rp/models
[ -f $M/Qwen3-8B-r1/config.json ] || CUDA_VISIBLE_DEVICES="" $PY merge_lora.py --adapter /tmp/xiang_rp/e1v2/impall --out $M/Qwen3-8B-r1 > $R/merge_r1.log 2>&1 || { echo "merge failed"; exit 1; }
echo "merged $(date)"
until grep -q "E0G2 ADAPTERS DONE\|impall2" $R/run_e0g2_adapters.log 2>/dev/null || [ -s ~/Role-Play-Game-NPC/exp/results/e0g2_minimalpair_impall2.txt ]; do sleep 30; done
until ! nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 0 | grep -q .; do sleep 20; done
nohup ~/rp_persona/scripts/serve.sh $M/Qwen3-8B-r1 0 1 8006 q8r1 > $R/serve_r1.log 2>&1 &
until curl -s http://localhost:8006/v1/models | grep -q q8r1; do sleep 10; done
until grep -q "q32 restored" $R/xjudge_closed_run.log; do sleep 20; done
echo "r1 + q32 up $(date)"
$PY e1v4_data.py --policy_url http://localhost:8006/v1 --policy_name q8r1 --policy_tok $M/Qwen3-8B-r1 --n_convs 128 > $R/e1v4_data.log 2>&1 || { echo "data failed"; exit 1; }
echo "data done $(date)"
$PY e1v4_pairs.py > $R/e1v4_pairs.log 2>&1; cat $R/e1v4_pairs.log
for p in $(pgrep -f "[s]erved-model-name q8r1 "); do kill $p; done; sleep 15
for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 0); do kill $p; done; sleep 5
CUDA_VISIBLE_DEVICES=0 $PY e1_train.py --algo dpo --lr 5e-5 --model $M/Qwen3-8B-r1 --data ~/rp_persona/data/e1v4/dpo_r2.jsonl --out /tmp/xiang_rp/e1v4/r2 > $R/e1v4_train.log 2>&1 || { echo "train failed"; exit 1; }
echo "r2 trained $(date)"
CUDA_VISIBLE_DEVICES=0 nohup $PY -m vllm.entrypoints.openai.api_server --model $M/Qwen3-8B-r1 --served-model-name q8r1 --port 8007 \
  --max-model-len 20480 --gpu-memory-utilization 0.90 --enable-prefix-caching --disable-log-requests \
  --enable-lora --max-lora-rank 16 --max-loras 2 --lora-modules r2=/tmp/xiang_rp/e1v4/r2 > $R/serve_r2.log 2>&1 &
until curl -s http://localhost:8007/v1/models | grep -q '"r2"'; do sleep 10; done
echo "r2 server up $(date)"
$PY e0c_stress.py --tag r2_her --mode her --policy_url http://localhost:8007/v1 --policy_name r2 --policy_tok $M/Qwen3-8B-r1 \
  --sim_url http://localhost:8000/v1 > $R/e0c_r2.log 2>&1 || { echo "closed loop failed"; exit 1; }
echo "r2 closed-loop gen done $(date)"
$PY e0c_judge.py --probes ~/rp_persona/data/e0c_probes_v1.jsonl --inp $R/e0c/e0c_r2_her.jsonl > $R/e0c_judge_r2.log 2>&1
echo "ALL DONE $(date)"
