#!/bin/bash
# usage: run_models.sh GPU:TAG:KIND:PATH ...   (runs sequentially per GPU group in background)
PY=$HOME/miniconda3/envs/verl-clean/bin/python
cd $HOME/rp_prior; mkdir -p runs/${EXP:-e1}
for spec in "$@"; do
  IFS=: read gpu tag kind path <<< "$spec"
  ( CUDA_VISIBLE_DEVICES=$gpu $PY src/score_ab.py "$path" $tag $kind data/${EXP:-e1}_prompts.jsonl runs/${EXP:-e1}/$tag.jsonl > runs/${EXP:-e1}/$tag.log 2>&1 ) &
  echo "$tag on $gpu pid $!"
done
