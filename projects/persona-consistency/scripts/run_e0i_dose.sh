#!/bin/bash
# E0-I dose response: anchor steering at 2x and 4x the measured drift (fixed PYTHONHASHSEED so seeds match across runs).
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; export PYTHONHASHSEED=0
(
  until grep -q "ANCHOR LINK DONE" $R/run_anchor_link.log; do sleep 30; done
  CUDA_VISIBLE_DEVICES=0 $PY e0i_steer.py --scale 2 --conds none,anchor --out $R/e0i/dose_x2.jsonl > $R/e0i_dose2.log 2>&1
  echo "x2 done $(date)"
) &
(
  until grep -q "ddpo closed-loop gen done\|ddpo closed loop failed" $R/after_e0i.log; do sleep 30; done
  for p in $(pgrep -f "[l]ora-modules ddpo="); do kill $p; done; sleep 15
  for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 1); do kill $p; done; sleep 5
  CUDA_VISIBLE_DEVICES=1 $PY e0i_steer.py --scale 4 --conds anchor --out $R/e0i/dose_x4.jsonl > $R/e0i_dose4.log 2>&1
  echo "x4 done $(date)"
) &
wait
sed 's/"policy": "steer:anchor"/"policy": "steer:anchor_x2"/' $R/e0i/dose_x2.jsonl > $R/e0i/dose_all.jsonl
sed 's/"policy": "steer:anchor"/"policy": "steer:anchor_x4"/' $R/e0i/dose_x4.jsonl >> $R/e0i/dose_all.jsonl
$PY e0c_judge.py --inp $R/e0i/dose_all.jsonl > $R/e0i_dose_judge.log 2>&1
echo "DOSE DONE $(date)"
