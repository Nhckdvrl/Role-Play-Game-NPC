#!/bin/bash
# r2': round 2 redone from r1 (implicit-all merged) with the full multi-objective setup from the start
# (7 probe types incl. benign_q / none / assistant_task; hostility and evasion count as failures), 1 epoch lr 5e-5.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; M=/tmp/xiang_rp/models; H=~/rp_persona/data/e0c_probes_heldout.jsonl
for p in $(pgrep -f "[s]erved-model-name q8r2 "); do kill $p; done; sleep 15
for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 0,1); do kill $p; done; sleep 5
nohup ~/rp_persona/scripts/serve.sh $M/Qwen3-8B-r1 0 1 8016 q8r1 > $R/serve_r1p.log 2>&1 &
until curl -s http://localhost:8016/v1/models | grep -q q8r1; do sleep 10; done
echo "r1 up $(date)"
$PY e1v5_data.py --policy_url http://localhost:8016/v1 --policy_name q8r1 --policy_tok $M/Qwen3-8B-r1 --n_convs 96 \
  --out $R/e1/r2p_data.jsonl > $R/r2p_data.log 2>&1 || { echo "data failed"; exit 1; }
echo "data done $(date)"
$PY e1v5_pairs.py --data $R/e1/r2p_data.jsonl --out ~/rp_persona/data/r2p/dpo_r2p.jsonl > $R/r2p_pairs.log 2>&1; cat $R/r2p_pairs.log
for p in $(pgrep -f "[s]erved-model-name q8r1 --tensor-parallel-size 1 --port 8016"); do kill $p; done; sleep 15
for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 0); do kill $p; done; sleep 5
CUDA_VISIBLE_DEVICES=0 $PY e1_train.py --algo dpo --lr 5e-5 --epochs 1 --model $M/Qwen3-8B-r1 --data ~/rp_persona/data/r2p/dpo_r2p.jsonl --out /tmp/xiang_rp/r2p > $R/r2p_train.log 2>&1 || { echo "train failed"; exit 1; }
echo "r2p trained $(date)"
CUDA_VISIBLE_DEVICES=0 nohup $PY -m vllm.entrypoints.openai.api_server --model $M/Qwen3-8B-r1 --served-model-name q8r1 --port 8017 \
  --max-model-len 20480 --gpu-memory-utilization 0.90 --enable-prefix-caching --disable-log-requests \
  --enable-lora --max-lora-rank 16 --max-loras 2 --lora-modules r2p=/tmp/xiang_rp/r2p > $R/serve_r2p.log 2>&1 &
until curl -s http://localhost:8017/v1/models | grep -q '"r2p"'; do sleep 10; done
echo "r2p server up $(date)"
U="--policy_url http://localhost:8017/v1 --policy_name r2p --policy_tok $M/Qwen3-8B-r1"
$PY e0c_stress.py --tag r2p_her --mode her $U --sim_url http://localhost:8000/v1 > $R/e0c_r2p.log 2>&1 || { echo "closed loop failed"; exit 1; }
$PY e0d_mechanism.py --probes $H $U --policy_label r2p --depth 20 --conds full --n 4 --probe_types false_q,meta_p1,meta_p2,meta_p3,benign_q --out $R/e1/heldout_r2p_d20.jsonl > $R/heldout_r2p.log 2>&1
$PY e0d_mechanism.py $U --policy_label r2p --depth 20 --conds full --n 8 --sample_offset 100 --probe_types false_premise,meta_ai,true_premise,none --out $R/e1/evalv6_r2p_d20.jsonl > $R/eval_r2p.log 2>&1
$PY gen_apc_server.py --url http://localhost:8017/v1 --models r2p --tok $M/Qwen3-8B-r1 > $R/apc_r2p_gen.log 2>&1
echo "r2p gen done $(date)"
$PY e0c_judge.py --probes ~/rp_persona/data/e0c_probes_v1.jsonl --inp $R/e0c/e0c_r2p_her.jsonl > $R/e0c_judge_r2p.log 2>&1
$PY e0c_judge.py --probes $H --inp $R/e1/heldout_r2p_d20.jsonl >> $R/e0c_judge_r2p.log 2>&1
$PY e0c_judge.py --inp $R/e1/evalv6_r2p_d20.jsonl >> $R/e0c_judge_r2p.log 2>&1
$PY judge_hostility.py --tags r2p_her > $R/hostility_r2p.log 2>&1
CUDA_VISIBLE_DEVICES=1 $PY score_apc.py --gen $R/e0a/gen_srv_r2p.jsonl > $R/apc_r2p_score.log 2>&1
echo "ALL DONE $(date)"
