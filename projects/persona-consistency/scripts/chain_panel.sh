#!/bin/bash
# E0-M grounding probe (2x2 minimal pairs x depth 2/10/20, fixed base histories) across a model panel on fvcrc10.
# Judge = Qwen3-32B already served on GPUs 2,3 (port 8000). Panel models rotate on GPUs 0,1. Plain mode for every model
# (cross-family comparability); HER mode additionally for the HER-format family (Qwen3-8B, our trained policies, Qwen3-32B, HER-32B).
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; O=$R/e0m; M=/tmp/xiang_rp/models; HF=~/.cache/huggingface/hub
mkdir -p $O
snap() { ls -d $HF/models--$1/snapshots/*/ | head -1; }
until grep -qE "ALL DONE|failed" $R/chain_r2pp_s1.log; do sleep 60; done
for p in $(pgrep -f "[s]erved-model-name q8r1 --port 8017"); do kill $p; done; sleep 15
for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 0,1); do kill $p; done; sleep 5
echo "start $(date)"
serve() {  # path gpus tp port name [extra]
  CUDA_VISIBLE_DEVICES=$2 nohup $PY -m vllm.entrypoints.openai.api_server --model $1 --served-model-name $5 --tensor-parallel-size $3 --port $4 \
    --max-model-len 20480 --gpu-memory-utilization 0.90 --disable-log-requests ${6:-} > $R/e0m/serve_$5.log 2>&1 &
  for i in $(seq 1 240); do curl -s http://localhost:$4/v1/models | grep -q "\"$5\"" && return 0; grep -q "Traceback" $R/e0m/serve_$5.log && break; sleep 15; done
  echo "serve $5 FAILED"; return 1
}
stop() { for p in $(pgrep -f "[s]erved-model-name $1 "); do kill $p; done; sleep 10; for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i $2); do kill $p; done; sleep 10; }
probe() {  # url name tok label mode [flags]
  $PY e0m_grounding.py --policy_url $1 --policy_name $2 --policy_tok $3 --label $4 --mode $5 ${6:-} --out $O/$4_$5.jsonl > $O/gen_$4_$5.log 2>&1 && \
  $PY e0m_judge.py --inp $O/$4_$5.jsonl --url http://localhost:8000/v1 >> $O/judge.log 2>&1
}
pair() {  # two single-GPU models in parallel, plain mode: path1 name1 label1 flags1 | path2 name2 label2 flags2 ("-" = none)
  P=""
  f1=$4; [ "$f1" = "-" ] && f1=""; f2=$8; [ "$f2" = "-" ] && f2=""
  if serve $1 0 1 8031 $2; then probe http://localhost:8031/v1 $2 $1 $3 plain "$f1" & P="$P $!"; fi
  if serve $5 1 1 8032 $6; then probe http://localhost:8032/v1 $6 $5 $7 plain "$f2" & P="$P $!"; fi
  wait $P; stop $2 0; stop $6 1
}
# Qwen3-32B is the judge server itself: probe it directly (plain + HER)
probe http://localhost:8000/v1 q32 $M/Qwen3-32B qwen3_32b plain &
PJ=$!
# our HER-format family: base Qwen3-8B + trained policies (LoRA on merged r1, and r2 adapters)
CUDA_VISIBLE_DEVICES=0 nohup $PY -m vllm.entrypoints.openai.api_server --model $M/Qwen3-8B-r1 --served-model-name q8r1 --port 8017 \
  --max-model-len 20480 --gpu-memory-utilization 0.90 --disable-log-requests --enable-lora --max-lora-rank 16 --max-loras 4 \
  --lora-modules r2=/tmp/xiang_rp/e1v4/r2 r2p2=/tmp/xiang_rp/r2p2 r2pp=/tmp/xiang_rp/r2pp > $R/e0m/serve_q8r1.log 2>&1 &
serve $M/Qwen3-8B 1 1 8032 q8
until curl -s http://localhost:8017/v1/models | grep -q '"r2pp"'; do sleep 15; done
P=""
for m in plain her; do probe http://localhost:8032/v1 q8 $M/Qwen3-8B qwen3_8b $m; done & P="$P $!"
(for a in q8r1:r1 r2:r2 r2p2:r2p2 r2pp:r2pp; do n=${a%%:*}; l=${a##*:}; probe http://localhost:8017/v1 $n $M/Qwen3-8B-r1 ours_$l her; done) & P="$P $!"
wait $P $PJ
probe http://localhost:8000/v1 q32 $M/Qwen3-32B qwen3_32b her
stop q8r1 0; stop q8 1
echo "family done $(date)"
# HER-32B (role-play RL on Qwen3-32B): TP2 on GPUs 0,1
if serve $(snap ChengyuDu0123--HER-32B) 0,1 2 8031 her32; then
  for m in plain her; do probe http://localhost:8031/v1 her32 $(snap ChengyuDu0123--HER-32B) her32b $m; done
fi
stop her32 0,1
echo "HER done $(date)"
pair $(snap Qwen--Qwen3-14B) q14 qwen3_14b -  $(snap Qwen--Qwen3-4B) q4 qwen3_4b -
pair $(snap meta-llama--Llama-3.1-8B-Instruct) llama8 llama31_8b -  $(snap google--gemma-3-4b-it) gemma4 gemma3_4b --no_think_flag
pair $(snap google--gemma-3-12b-it) gemma12 gemma3_12b --no_think_flag  $(snap microsoft--Phi-4-mini-instruct) phi4m phi4mini -
if serve $(snap mistralai--Mistral-Small-24B-Instruct-2501) 0,1 2 8031 msmall; then
  probe http://localhost:8031/v1 msmall $(snap mistralai--Mistral-Small-24B-Instruct-2501) mistral_small24b plain
fi
stop msmall 0,1
if serve $(snap Qwen--Qwen3-30B-A3B) 0,1 2 8031 q30a3; then
  probe http://localhost:8031/v1 q30a3 $(snap Qwen--Qwen3-30B-A3B) qwen3_30b_a3b plain
fi
stop q30a3 0,1
echo "ALL DONE $(date)"
