#!/bin/bash
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
until grep -q "q32 restored" ~/rp_persona/runs/xjudge_closed_run.log; do sleep 20; done
$PY e0c_judge.py --inp ~/rp_persona/runs/e0i/dose_all.jsonl > ~/rp_persona/runs/e0i_dose_judge.log 2>&1
echo "DOSE JUDGED $(date)"
