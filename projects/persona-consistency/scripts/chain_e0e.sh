#!/bin/bash
# E0-E: non-privileged self-check vs default, with true-premise and natural controls, at depth 2 and 20.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
until curl -s http://localhost:8000/v1/models | grep -q q32 && curl -s http://localhost:8001/v1/models | grep -q q8; do sleep 10; done
echo "servers up $(date)"
$PY gen_true_probes.py > ~/rp_persona/runs/e0e_trueprobes.log 2>&1 || { echo "trueprobes failed"; exit 1; }
for D in 20 2; do
  $PY e0d_mechanism.py --depth $D --conds full,selfcheck_dir,selfcheck_sys --probe_types false_premise,true_premise,none,meta_ai \
     --out ~/rp_persona/runs/e0e/e0e_q8her_d$D.jsonl > ~/rp_persona/runs/e0e_d$D.log 2>&1 || { echo "gen d$D failed"; exit 1; }
done
echo "gen done $(date)"
$PY e0c_judge.py --inp ~/rp_persona/runs/e0e/e0e_q8her_d20.jsonl ~/rp_persona/runs/e0e/e0e_q8her_d2.jsonl > ~/rp_persona/runs/e0e_judge.log 2>&1 || { echo "judge failed"; exit 1; }
echo "ALL DONE $(date)"
