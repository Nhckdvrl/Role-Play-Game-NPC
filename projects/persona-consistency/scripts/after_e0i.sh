#!/bin/bash
# After E0-I generation: judge E0-I; rerun the distill-DPO closed loop with its adapter served on GPU1 (GPU0 runs the anchor-link test).
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs
until grep -q "steer gen done" $R/run_e0i.log; do sleep 30; done
for p in $(pgrep -f "[r]un_e0i.sh"); do kill $p; done   # its final wait would never end
$PY e0c_judge.py --inp $R/e0i/steer_d20.jsonl > $R/e0i_judge.log 2>&1 && echo "E0I JUDGED $(date)" &
JP=$!
TP=1 nohup ~/rp_persona/scripts/serve_lora.sh 1 8001 ddpo=/tmp/xiang_rp/e1v3/ddpo > $R/serve_lora_ddpo.log 2>&1 &
until curl -s http://localhost:8001/v1/models | grep -q ddpo; do sleep 10; done
echo "ddpo server up $(date)"
$PY e0c_stress.py --tag ddpo_her --mode her --policy_url http://localhost:8001/v1 --policy_name ddpo \
  --policy_tok /tmp/xiang_rp/models/Qwen3-8B --sim_url http://localhost:8000/v1 > $R/e0c_ddpo.log 2>&1 || { echo "ddpo closed loop failed"; exit 1; }
echo "ddpo closed-loop gen done $(date)"
wait $JP
$PY e0c_judge.py --probes ~/rp_persona/data/e0c_probes_v1.jsonl --inp $R/e0c/e0c_ddpo_her.jsonl > $R/e0c_judge_ddpo.log 2>&1
echo "AFTER E0I DONE $(date)"
