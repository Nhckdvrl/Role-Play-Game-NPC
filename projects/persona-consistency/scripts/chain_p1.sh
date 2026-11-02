#!/bin/bash
# P1 selectivity eval: in-story AI challenge (stay in character) vs OUT-OF-CHARACTER sincere AI question / legitimate
# OOC request (step out). D=20 fixed base histories, 4 samples per probe; base, r1, r2, r2', r2'-2ep.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; M=/tmp/xiang_rp/models; O=~/rp_persona/data/e0c_probes_ooc.jsonl
PT=meta_ai,ooc_ai_1,ooc_ai_2,ooc_ai_3,ooc_req_1,ooc_req_2
for p in $(pgrep -f "[s]erved-model-name q8r1 --port 8017"); do kill $p; done; sleep 15
for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 0,1); do kill $p; done; sleep 5
CUDA_VISIBLE_DEVICES=0 nohup $PY -m vllm.entrypoints.openai.api_server --model $M/Qwen3-8B-r1 --served-model-name q8r1 --port 8017 \
  --max-model-len 20480 --gpu-memory-utilization 0.90 --enable-prefix-caching --disable-log-requests \
  --enable-lora --max-lora-rank 16 --max-loras 3 --lora-modules r2=/tmp/xiang_rp/e1v4/r2 r2p=/tmp/xiang_rp/r2p r2p2=/tmp/xiang_rp/r2p2 > $R/serve_p1_r1.log 2>&1 &
nohup ~/rp_persona/scripts/serve.sh $M/Qwen3-8B 1 1 8010 q8 > $R/serve_p1_base.log 2>&1 &
until curl -s http://localhost:8017/v1/models | grep -q '"r2p2"' && curl -s http://localhost:8010/v1/models | grep -q '"q8"'; do sleep 10; done
echo "servers up $(date)"
run() {  # label url name tok
  $PY e0d_mechanism.py --probes $O --policy_url $2 --policy_name $3 --policy_tok $4 --policy_label $1 --depth 20 --conds full --n 4 \
    --sample_offset 200 --probe_types $PT --out $R/e1/p1_$1_d20.jsonl > $R/p1_$1.log 2>&1 && \
  $PY e0c_judge.py --probes $O --inp $R/e1/p1_$1_d20.jsonl >> $R/p1_judge.log 2>&1
}
P=""
run base http://localhost:8010/v1 q8 $M/Qwen3-8B & P="$P $!"
run r1 http://localhost:8017/v1 q8r1 $M/Qwen3-8B-r1 & P="$P $!"
run r2 http://localhost:8017/v1 r2 $M/Qwen3-8B-r1 & P="$P $!"
run r2p http://localhost:8017/v1 r2p $M/Qwen3-8B-r1 & P="$P $!"
run r2p2 http://localhost:8017/v1 r2p2 $M/Qwen3-8B-r1 & P="$P $!"
wait $P   # explicit PIDs only: never wait on the background servers
echo "ALL DONE $(date)"
