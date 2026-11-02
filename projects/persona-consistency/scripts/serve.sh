#!/bin/bash
# usage: serve.sh <model_path> <gpus> <tp> <port> <name>
PY=~/miniconda3/envs/verl-clean/bin/python
CUDA_VISIBLE_DEVICES=$2 exec $PY -m vllm.entrypoints.openai.api_server --model $1 --served-model-name $5 \
  --tensor-parallel-size $3 --port $4 --max-model-len 20480 --gpu-memory-utilization 0.90 \
  --enable-prefix-caching --disable-log-requests
