#!/bin/bash
# r2'': r2' balanced data + should-yield OOC pairs (sincere OOC "are you an AI?" -> honest disclosure; legitimate OOC
# request -> honor it), all sampled from r1 on the same training contexts. 2 epochs lr 5e-5 DDP GPU0,1 from r1.
# Tests whether balanced on-policy data also restores in-story vs out-of-story selectivity (P1 found r2 / r2'-2ep lose it).
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; M=/tmp/xiang_rp/models; H=~/rp_persona/data/e0c_probes_heldout.jsonl; O=~/rp_persona/data/e0c_probes_ooc.jsonl
for p in $(pgrep -f "[s]erved-model-name q8 --tensor-parallel-size 1 --port 8010"); do kill $p; done
$PY e1r4_ooc_data.py > $R/r4_ooc_data.log 2>&1 || { echo "data failed"; exit 1; }
echo "ooc data done $(date)"
$PY e1v5_pairs.py --data $R/e1/r4_ooc_data.jsonl --out ~/rp_persona/data/r2pp/dpo_ooc.jsonl --tok $M/Qwen3-8B-r1 > $R/r2pp_pairs.log 2>&1; cat $R/r2pp_pairs.log
cat ~/rp_persona/data/r2p/dpo_r2p.jsonl ~/rp_persona/data/r2pp/dpo_ooc.jsonl > ~/rp_persona/data/r2pp/dpo_r2pp.jsonl
for p in $(pgrep -f "[s]erved-model-name q8r1 --port 8017"); do kill $p; done; sleep 15
for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 0,1); do kill $p; done; sleep 5
CUDA_VISIBLE_DEVICES=0,1 ~/miniconda3/envs/verl-clean/bin/accelerate launch --num_processes 2 --mixed_precision bf16 \
  e1_train.py --algo dpo --lr 5e-5 --epochs 2 --grad_acc 4 --model $M/Qwen3-8B-r1 --data ~/rp_persona/data/r2pp/dpo_r2pp.jsonl \
  --out /tmp/xiang_rp/r2pp > $R/r2pp_train.log 2>&1 || { echo "train failed"; exit 1; }
echo "r2pp trained $(date)"
CUDA_VISIBLE_DEVICES=0 nohup $PY -m vllm.entrypoints.openai.api_server --model $M/Qwen3-8B-r1 --served-model-name q8r1 --port 8017 \
  --max-model-len 20480 --gpu-memory-utilization 0.90 --enable-prefix-caching --disable-log-requests \
  --enable-lora --max-lora-rank 16 --max-loras 2 --lora-modules r2pp=/tmp/xiang_rp/r2pp > $R/serve_r2pp.log 2>&1 &
until curl -s http://localhost:8017/v1/models | grep -q '"r2pp"'; do sleep 10; done
echo "r2pp server up $(date)"
U="--policy_url http://localhost:8017/v1 --policy_name r2pp --policy_tok $M/Qwen3-8B-r1"
$PY e0c_stress.py --tag r2pp_her --mode her $U --sim_url http://localhost:8000/v1 > $R/e0c_r2pp.log 2>&1 || { echo "closed loop failed"; exit 1; }
$PY e0d_mechanism.py --probes $H $U --policy_label r2pp --depth 20 --conds full --n 4 --probe_types false_q,meta_p1,meta_p2,meta_p3,benign_q --out $R/e1/heldout_r2pp_d20.jsonl > $R/heldout_r2pp.log 2>&1
$PY e0d_mechanism.py $U --policy_label r2pp --depth 20 --conds full --n 8 --sample_offset 100 --probe_types false_premise,meta_ai,true_premise,none --out $R/e1/evalv6_r2pp_d20.jsonl > $R/eval_r2pp.log 2>&1
$PY e0d_mechanism.py --probes $O $U --policy_label r2pp --depth 20 --conds full --n 4 --sample_offset 200 --probe_types meta_ai,ooc_ai_1,ooc_ai_2,ooc_ai_3,ooc_req_1,ooc_req_2 --out $R/e1/p1_r2pp_d20.jsonl > $R/p1_r2pp.log 2>&1
$PY gen_apc_server.py --url http://localhost:8017/v1 --models r2pp --tok $M/Qwen3-8B-r1 > $R/apc_r2pp_gen.log 2>&1
echo "r2pp gen done $(date)"
$PY e0c_judge.py --probes ~/rp_persona/data/e0c_probes_v1.jsonl --inp $R/e0c/e0c_r2pp_her.jsonl > $R/e0c_judge_r2pp.log 2>&1
$PY e0c_judge.py --probes $H --inp $R/e1/heldout_r2pp_d20.jsonl >> $R/e0c_judge_r2pp.log 2>&1
$PY e0c_judge.py --inp $R/e1/evalv6_r2pp_d20.jsonl >> $R/e0c_judge_r2pp.log 2>&1
$PY e0c_judge.py --probes $O --inp $R/e1/p1_r2pp_d20.jsonl >> $R/e0c_judge_r2pp.log 2>&1
$PY judge_hostility.py --tags r2pp_her > $R/hostility_r2pp.log 2>&1
CUDA_VISIBLE_DEVICES=1 $PY score_apc.py --gen $R/e0a/gen_srv_r2pp.jsonl > $R/apc_r2pp_score.log 2>&1
echo "ALL DONE $(date)"
