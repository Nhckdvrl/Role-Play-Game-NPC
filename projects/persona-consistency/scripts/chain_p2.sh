#!/bin/bash
# P2: swap the USER SIMULATOR (Qwen3-32B -> Mistral-Small-24B, a different model family) in the closed loop; same probes
# (e0c_probes_v1), same judge (Qwen3-32B). Tests whether the trained policies' gains depend on the training simulator.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; M=/tmp/xiang_rp/models
MS=$(ls -d ~/.cache/huggingface/hub/models--mistralai--Mistral-Small-24B-Instruct-2501/snapshots/*/)
for p in $(pgrep -f "[s]erved-model-name q8r1 --port 8017"); do kill $p; done
for p in $(pgrep -f "[s]erved-model-name q8 --tensor-parallel-size 1 --port 8010"); do kill $p; done; sleep 15
for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 0,1); do kill $p; done; sleep 5
CUDA_VISIBLE_DEVICES=0 nohup $PY -m vllm.entrypoints.openai.api_server --model $M/Qwen3-8B-r1 --served-model-name q8r1 --port 8017 \
  --max-model-len 20480 --gpu-memory-utilization 0.45 --enable-prefix-caching --disable-log-requests \
  --enable-lora --max-lora-rank 16 --max-loras 2 --lora-modules r2p2=/tmp/xiang_rp/r2p2 r2pp=/tmp/xiang_rp/r2pp > $R/serve_p2_r1.log 2>&1 &
sleep 90
CUDA_VISIBLE_DEVICES=0 nohup $PY -m vllm.entrypoints.openai.api_server --model $M/Qwen3-8B --served-model-name q8 --port 8010 \
  --max-model-len 20480 --gpu-memory-utilization 0.45 --enable-prefix-caching --disable-log-requests > $R/serve_p2_base.log 2>&1 &
nohup ~/rp_persona/scripts/serve.sh $MS 1 1 8004 mistral > $R/serve_p2_mistral.log 2>&1 &
until curl -s http://localhost:8017/v1/models | grep -q '"r2pp"' && curl -s http://localhost:8010/v1/models | grep -q '"q8"' && curl -s http://localhost:8004/v1/models | grep -q mistral; do sleep 15; done
echo "servers up $(date)"
S="--sim_url http://localhost:8004/v1 --sim_name mistral --sim_tok $MS"
P=""
$PY e0c_stress.py --tag q8her_msim --mode her --policy_url http://localhost:8010/v1 --policy_name q8 --policy_tok $M/Qwen3-8B $S > $R/e0c_q8_msim.log 2>&1 & P="$P $!"
$PY e0c_stress.py --tag r2p2_msim --mode her --policy_url http://localhost:8017/v1 --policy_name r2p2 --policy_tok $M/Qwen3-8B-r1 $S > $R/e0c_r2p2_msim.log 2>&1 & P="$P $!"
$PY e0c_stress.py --tag r2pp_msim --mode her --policy_url http://localhost:8017/v1 --policy_name r2pp --policy_tok $M/Qwen3-8B-r1 $S > $R/e0c_r2pp_msim.log 2>&1 & P="$P $!"
wait $P
echo "closed loops done $(date)"
for t in q8her_msim r2p2_msim r2pp_msim; do
  $PY e0c_judge.py --probes ~/rp_persona/data/e0c_probes_v1.jsonl --inp $R/e0c/e0c_$t.jsonl >> $R/e0c_judge_msim.log 2>&1
done
$PY judge_hostility.py --tags q8her_msim,r2p2_msim,r2pp_msim > $R/hostility_msim.log 2>&1
echo "ALL DONE $(date)"
