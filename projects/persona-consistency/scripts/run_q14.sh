#!/bin/bash
# External validity: closed-loop E0-C protocol with Qwen3-14B (HER mode), same probes / simulator / judge as Qwen3-8B.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs
until ! nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 1 | grep -q .; do sleep 20; done
nohup ~/rp_persona/scripts/serve.sh /home/xiang/.cache/huggingface/hub/models--Qwen--Qwen3-14B/snapshots/40c069824f4251a91eefaf281ebe4c544efd3e18/ 1 1 8015 q14 > $R/serve_q14.log 2>&1 &
SP=$!
until curl -s http://localhost:8015/v1/models | grep -q q14; do sleep 15; done
$PY e0c_stress.py --tag q14her --mode her --policy_url http://localhost:8015/v1 --policy_name q14 --policy_tok /home/xiang/.cache/huggingface/hub/models--Qwen--Qwen3-14B/snapshots/40c069824f4251a91eefaf281ebe4c544efd3e18/ --sim_url http://localhost:8000/v1 > $R/e0c_q14.log 2>&1
kill $SP; sleep 10; for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 1); do kill $p; done
$PY e0c_judge.py --probes ~/rp_persona/data/e0c_probes_v1.jsonl --inp $R/e0c/e0c_q14her.jsonl > $R/e0c_judge_q14.log 2>&1
echo "Q14 DONE $(date)"
