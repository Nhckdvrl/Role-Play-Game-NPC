#!/bin/bash
# Second independent closed-loop replicate (new seeds) for base and implicit-all on GPU1, to raise power.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs
until ! nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 1 | grep -q .; do sleep 30; done
until grep -q "q32 restored" $R/xjudge_rep2_run.log; do sleep 20; done
TP=1 nohup ~/rp_persona/scripts/serve_lora.sh 1 8010 impall2=/tmp/xiang_rp/e1v2/impall > $R/serve_rep3.log 2>&1 &
until curl -s http://localhost:8010/v1/models | grep -q impall2; do sleep 10; done
PIDS=""
for A in q8:q8her_s2 impall2:impall2_her_s2; do
  N=${A%%:*}; T=${A#*:}
  $PY e0c_stress.py --tag $T --mode her --seed_offset 1555 --policy_url http://localhost:8010/v1 --policy_name $N \
    --policy_tok /tmp/xiang_rp/models/Qwen3-8B --sim_url http://localhost:8000/v1 > $R/e0c_$T.log 2>&1 &
  PIDS="$PIDS $!"
done
wait $PIDS
echo "rep3 gen done $(date)"
$PY e0c_judge.py --probes ~/rp_persona/data/e0c_probes_v1.jsonl --inp $R/e0c/e0c_q8her_s2.jsonl $R/e0c/e0c_impall2_her_s2.jsonl > $R/e0c_judge_rep3.log 2>&1
echo "REP3 DONE $(date)"
