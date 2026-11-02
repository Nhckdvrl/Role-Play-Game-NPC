#!/bin/bash
# r2'-2ep: same r2' pairs (from r1, 7 probe types, hostility/evasion = failure), 2 epochs lr 5e-5 (r2 strength),
# DDP on GPU0,1 with grad_acc 4 (same effective batch 8). Tests whether r2' avoided over-guardedness only because it learned less.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; M=/tmp/xiang_rp/models; H=~/rp_persona/data/e0c_probes_heldout.jsonl
for p in $(pgrep -f "[s]erved-model-name q8r1 --port 8017"); do kill $p; done; sleep 15
for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 0,1); do kill $p; done; sleep 5
CUDA_VISIBLE_DEVICES=0,1 ~/miniconda3/envs/verl-clean/bin/accelerate launch --num_processes 2 --mixed_precision bf16 \
  e1_train.py --algo dpo --lr 5e-5 --epochs 2 --grad_acc 4 --model $M/Qwen3-8B-r1 --data ~/rp_persona/data/r2p/dpo_r2p.jsonl \
  --out /tmp/xiang_rp/r2p2 > $R/r2p2_train.log 2>&1 || { echo "train failed"; exit 1; }
echo "r2p2 trained $(date)"
CUDA_VISIBLE_DEVICES=0 nohup $PY -m vllm.entrypoints.openai.api_server --model $M/Qwen3-8B-r1 --served-model-name q8r1 --port 8017 \
  --max-model-len 20480 --gpu-memory-utilization 0.90 --enable-prefix-caching --disable-log-requests \
  --enable-lora --max-lora-rank 16 --max-loras 2 --lora-modules r2p2=/tmp/xiang_rp/r2p2 > $R/serve_r2p2.log 2>&1 &
until curl -s http://localhost:8017/v1/models | grep -q '"r2p2"'; do sleep 10; done
echo "r2p2 server up $(date)"
U="--policy_url http://localhost:8017/v1 --policy_name r2p2 --policy_tok $M/Qwen3-8B-r1"
$PY e0c_stress.py --tag r2p2_her --mode her $U --sim_url http://localhost:8000/v1 > $R/e0c_r2p2.log 2>&1 || { echo "closed loop failed"; exit 1; }
$PY e0d_mechanism.py --probes $H $U --policy_label r2p2 --depth 20 --conds full --n 4 --probe_types false_q,meta_p1,meta_p2,meta_p3,benign_q --out $R/e1/heldout_r2p2_d20.jsonl > $R/heldout_r2p2.log 2>&1
$PY e0d_mechanism.py $U --policy_label r2p2 --depth 20 --conds full --n 8 --sample_offset 100 --probe_types false_premise,meta_ai,true_premise,none --out $R/e1/evalv6_r2p2_d20.jsonl > $R/eval_r2p2.log 2>&1
$PY gen_apc_server.py --url http://localhost:8017/v1 --models r2p2 --tok $M/Qwen3-8B-r1 > $R/apc_r2p2_gen.log 2>&1
echo "r2p2 gen done $(date)"
$PY e0c_judge.py --probes ~/rp_persona/data/e0c_probes_v1.jsonl --inp $R/e0c/e0c_r2p2_her.jsonl > $R/e0c_judge_r2p2.log 2>&1
$PY e0c_judge.py --probes $H --inp $R/e1/heldout_r2p2_d20.jsonl >> $R/e0c_judge_r2p2.log 2>&1
$PY e0c_judge.py --inp $R/e1/evalv6_r2p2_d20.jsonl >> $R/e0c_judge_r2p2.log 2>&1
$PY judge_hostility.py --tags r2p2_her > $R/hostility_r2p2.log 2>&1
CUDA_VISIBLE_DEVICES=1 $PY score_apc.py --gen $R/e0a/gen_srv_r2p2.jsonl > $R/apc_r2p2_score.log 2>&1
echo "ALL DONE $(date)"
