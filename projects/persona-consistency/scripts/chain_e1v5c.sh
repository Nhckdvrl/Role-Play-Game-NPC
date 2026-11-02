#!/bin/bash
# r3b: round-3 data with benign_q and none pairs up-weighted x2, lr 5e-5, 1 epoch; same evaluation plus benign/APC/hostility checks.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; M=/tmp/xiang_rp/models
for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 0); do kill $p; done; sleep 5
CUDA_VISIBLE_DEVICES=0 $PY e1_train.py --algo dpo --lr 5e-5 --epochs 1 --model $M/Qwen3-8B-r2 --data ~/rp_persona/data/e1v5/dpo_r3b.jsonl --out /tmp/xiang_rp/e1v5/r3b > $R/e1v5b_train.log 2>&1 || { echo "train failed"; exit 1; }
echo "r3b trained $(date)"
CUDA_VISIBLE_DEVICES=0 nohup $PY -m vllm.entrypoints.openai.api_server --model $M/Qwen3-8B-r2 --served-model-name q8r2 --port 8012 \
  --max-model-len 20480 --gpu-memory-utilization 0.90 --enable-prefix-caching --disable-log-requests \
  --enable-lora --max-lora-rank 16 --max-loras 2 --lora-modules r3b=/tmp/xiang_rp/e1v5/r3b > $R/serve_r3.log 2>&1 &
until curl -s http://localhost:8012/v1/models | grep -q '"r3b"'; do sleep 10; done
echo "r3b server up $(date)"
$PY e0c_stress.py --tag r3b_her --mode her --policy_url http://localhost:8012/v1 --policy_name r3b --policy_tok $M/Qwen3-8B-r2 \
  --sim_url http://localhost:8000/v1 > $R/e0c_r3b.log 2>&1 || { echo "closed loop failed"; exit 1; }
$PY e0d_mechanism.py --probes ~/rp_persona/data/e0c_probes_heldout.jsonl --policy_url http://localhost:8012/v1 --policy_name r3b \
  --policy_tok $M/Qwen3-8B-r2 --policy_label r3b --depth 20 --conds full --n 4 --probe_types false_q,meta_p1,meta_p2,meta_p3 \
  --out $R/e1/heldout_r3b_d20.jsonl > $R/heldout_r3b.log 2>&1
$PY e0d_mechanism.py --policy_url http://localhost:8012/v1 --policy_name r3b --policy_tok $M/Qwen3-8B-r2 --policy_label r3b --depth 20 \
  --conds full --n 8 --sample_offset 100 --probe_types false_premise,meta_ai,true_premise,none --out $R/e1/evalv5_r3b_d20.jsonl > $R/e1v5_eval_r3b.log 2>&1
echo "r3b gen done $(date)"
$PY e0c_judge.py --probes ~/rp_persona/data/e0c_probes_v1.jsonl --inp $R/e0c/e0c_r3b_her.jsonl > $R/e0c_judge_r3b.log 2>&1
$PY e0c_judge.py --probes ~/rp_persona/data/e0c_probes_heldout.jsonl --inp $R/e1/heldout_r3b_d20.jsonl >> $R/e0c_judge_r3b.log 2>&1
$PY e0c_judge.py --inp $R/e1/evalv5_r3b_d20.jsonl >> $R/e0c_judge_r3b.log 2>&1
$PY judge_hostility.py --tags r3b_her > $R/hostility_r3b.log 2>&1
H=~/rp_persona/data/e0c_probes_heldout.jsonl
$PY e0d_mechanism.py --probes $H --policy_url http://localhost:8012/v1 --policy_name r3b --policy_tok $M/Qwen3-8B-r2 --policy_label r3b \
  --depth 20 --conds full --n 4 --probe_types benign_q --out $R/e1/benign_r3b_d20.jsonl > $R/benign_r3b.log 2>&1
$PY gen_apc_server.py --url http://localhost:8012/v1 --models r3b --tok $M/Qwen3-8B-r2 > $R/apc_r3b_gen.log 2>&1
$PY e0c_judge.py --probes $H --inp $R/e1/benign_r3b_d20.jsonl > $R/benign_r3b_judge.log 2>&1
until ! nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 1 | grep -q .; do sleep 30; done
CUDA_VISIBLE_DEVICES=1 $PY score_apc.py --gen $R/e0a/gen_srv_r3b.jsonl > $R/apc_r3b_score.log 2>&1
echo "ALL DONE $(date)"
