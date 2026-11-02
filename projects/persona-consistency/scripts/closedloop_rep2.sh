#!/bin/bash
# Second independent closed-loop replicate (new seeds) for base and implicit-all on GPU1, to raise power.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs
until grep -q "E0G2 ADAPTERS DONE" $R/run_e0g2_adapters.log; do sleep 30; done
until grep -q "q32 restored" $R/xjudge_closed_run.log; do sleep 20; done
TP=1 nohup ~/rp_persona/scripts/serve_lora.sh 1 8008 impall2=/tmp/xiang_rp/e1v2/impall > $R/serve_rep2.log 2>&1 &
until curl -s http://localhost:8008/v1/models | grep -q impall2; do sleep 10; done
PIDS=""
for A in q8:q8her_s1 impall2:impall2_her_s1; do
  N=${A%%:*}; T=${A#*:}
  $PY e0c_stress.py --tag $T --mode her --seed_offset 777 --policy_url http://localhost:8008/v1 --policy_name $N \
    --policy_tok /tmp/xiang_rp/models/Qwen3-8B --sim_url http://localhost:8000/v1 > $R/e0c_$T.log 2>&1 &
  PIDS="$PIDS $!"
done
wait $PIDS
echo "rep2 gen done $(date)"
$PY e0c_judge.py --probes ~/rp_persona/data/e0c_probes_v1.jsonl --inp $R/e0c/e0c_q8her_s1.jsonl $R/e0c/e0c_impall2_her_s1.jsonl > $R/e0c_judge_rep2.log 2>&1
echo "REP2 DONE $(date)"
