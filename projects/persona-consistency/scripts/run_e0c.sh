#!/bin/bash
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
$PY e0c_stress.py --tag q8her --mode her > ~/rp_persona/runs/e0c_q8her.log 2>&1 &
until [ -s /home/xiang/rp_persona/data/e0c_probes_v1.jsonl ]; do sleep 5; done
sleep 5
$PY e0c_stress.py --tag q8plain --mode plain > ~/rp_persona/runs/e0c_q8plain.log 2>&1 &
wait
echo "GEN DONE $(date)"
$PY e0c_judge.py --inp ~/rp_persona/runs/e0c/e0c_q8her.jsonl ~/rp_persona/runs/e0c/e0c_q8plain.jsonl > ~/rp_persona/runs/e0c_judge_q8.log 2>&1
echo "JUDGE DONE $(date)"
