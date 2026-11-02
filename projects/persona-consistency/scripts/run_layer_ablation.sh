#!/bin/bash
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; A=/tmp/xiang_rp/e1v2/impall
$PY make_subset_adapters.py --adapter $A > $R/layer_ablation_make.log 2>&1
until ! nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 1 | grep -q .; do sleep 20; done
TP=1 nohup ~/rp_persona/scripts/serve_lora.sh 1 8014 early=${A}_early mid=${A}_mid late=${A}_late > $R/serve_layerabl.log 2>&1 &
SP=$!
until curl -s http://localhost:8014/v1/models | grep -q late; do sleep 10; done
PIDS=""
for S in early mid late; do
  $PY e0d_mechanism.py --policy_url http://localhost:8014/v1 --policy_name $S --policy_label impall2_$S --depth 20 --conds full --n 8 --sample_offset 100 \
    --probe_types false_premise,meta_ai --out $R/e1/layerabl_${S}_d20.jsonl > $R/layerabl_$S.log 2>&1 &
  PIDS="$PIDS $!"
done
wait $PIDS
kill $SP; sleep 10; for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 1); do kill $p; done
$PY e0c_judge.py --inp $R/e1/layerabl_early_d20.jsonl $R/e1/layerabl_mid_d20.jsonl $R/e1/layerabl_late_d20.jsonl > $R/layerabl_judge.log 2>&1
echo "LAYER ABLATION DONE $(date)"
