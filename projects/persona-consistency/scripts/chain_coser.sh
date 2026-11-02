#!/bin/bash
# CoSER GCA (200 test scenes) for base / r1 / r2'-2ep / r2'' once the r2'' chain and P3 are done.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; M=/tmp/xiang_rp/models
until grep -q "ALL DONE" $R/chain_r2pp_b.log && grep -q "P3 DONE" $R/e0l.log 2>/dev/null; do sleep 60; done
for p in $(pgrep -f "[s]erved-model-name q8r1 --port 8017"); do kill $p; done; sleep 15
for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 0,1); do kill $p; done; sleep 5
CUDA_VISIBLE_DEVICES=0 nohup $PY -m vllm.entrypoints.openai.api_server --model $M/Qwen3-8B-r1 --served-model-name q8r1 --port 8017 \
  --max-model-len 20480 --gpu-memory-utilization 0.90 --enable-prefix-caching --disable-log-requests \
  --enable-lora --max-lora-rank 16 --max-loras 2 --lora-modules r2p2=/tmp/xiang_rp/r2p2 r2pp=/tmp/xiang_rp/r2pp > $R/serve_coser_r1.log 2>&1 &
nohup ~/rp_persona/scripts/serve.sh $M/Qwen3-8B 1 1 8010 q8 > $R/serve_coser_base.log 2>&1 &
until curl -s http://localhost:8017/v1/models | grep -q '"r2pp"' && curl -s http://localhost:8010/v1/models | grep -q '"q8"'; do sleep 10; done
echo "servers up $(date)"
RT='{"q32": "http://localhost:8000/v1", "q8": "http://localhost:8010/v1", "q8r1": "http://localhost:8017/v1", "r2p2": "http://localhost:8017/v1", "r2pp": "http://localhost:8017/v1"}'
P=""
for a in q8 q8r1 r2p2 r2pp; do
  $PY run_coser_gca.py --actor $a --routes "$RT" --workers 40 > $R/coser_$a.log 2>&1 & P="$P $!"
done
wait $P
echo "ALL DONE $(date)"
