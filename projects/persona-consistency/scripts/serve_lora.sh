#!/bin/bash
# usage: serve_lora.sh <gpus> <port> name=path [name=path ...]   (base Qwen3-8B served as "q8")
PY=~/miniconda3/envs/verl-clean/bin/python
G=$1; PORT=$2; shift 2
CUDA_VISIBLE_DEVICES=$G exec $PY -m vllm.entrypoints.openai.api_server --model /tmp/xiang_rp/models/Qwen3-8B --served-model-name q8 \
  --port $PORT --max-model-len 20480 --gpu-memory-utilization 0.90 --enable-prefix-caching --disable-log-requests \
  --enable-lora --max-lora-rank 16 --max-loras 6 --tensor-parallel-size ${TP:-1} --lora-modules "$@"
