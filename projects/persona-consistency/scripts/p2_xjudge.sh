#!/bin/bash
# Mistral judge on the Mistral-simulator closed loops: main claim with no Qwen3-32B anywhere in the evaluation loop.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; MS=$(ls -d ~/.cache/huggingface/hub/models--mistralai--Mistral-Small-24B-Instruct-2501/snapshots/*/)
for t in q8her_msim r2p2_msim r2pp_msim; do
  $PY e0c_judge.py --probes ~/rp_persona/data/e0c_probes_v1.jsonl --inp $R/e0c/e0c_$t.jsonl --url http://localhost:8004/v1 --name mistral --tok $MS --out_suffix .judge_mistral.jsonl >> $R/p2_xjudge.log 2>&1
done
echo "ALL DONE $(date)" >> $R/p2_xjudge.log
