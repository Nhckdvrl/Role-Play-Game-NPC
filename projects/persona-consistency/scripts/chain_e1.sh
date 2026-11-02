#!/bin/bash
# E1: label directors -> pairs -> train 3 arms (+ activation features) -> serve adapters -> eval -> judge.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; D=~/rp_persona/data/e1; A=/tmp/xiang_rp/e1
until grep -qE "ALL DONE|failed" $R/run_e1data.log; do sleep 30; done
grep -q "ALL DONE" $R/run_e1data.log || { echo "data failed"; exit 1; }
echo "data done $(date)"
pkill -f "served-model-name q8 "; sleep 20
$PY e1_label_directors.py $R/e1/e1_data_v1.jsonl > $R/e1_label.log 2>&1 || { echo "label failed"; exit 1; }
$PY e1_pairs.py > $R/e1_pairs.log 2>&1 || { echo "pairs failed"; exit 1; }
cat $R/e1_pairs.log
mkdir -p $A
CUDA_VISIBLE_DEVICES=0 $PY e1_train.py --algo dpo --data $D/dpo_implicit.jsonl --out $A/dpo_implicit > $R/e1_train_imp.log 2>&1 &
CUDA_VISIBLE_DEVICES=1 $PY e1_train.py --algo dpo --data $D/dpo_explicit.jsonl --out $A/dpo_explicit > $R/e1_train_exp.log 2>&1
wait
echo "dpo trained $(date)"
CUDA_VISIBLE_DEVICES=0 $PY e1_train.py --algo sft --data $D/sft_rft.jsonl --out $A/sft_rft > $R/e1_train_sft.log 2>&1 &
CUDA_VISIBLE_DEVICES=1 $PY e0g_actprobe.py > $R/e0g_feats.log 2>&1
wait
echo "sft + feats done $(date)"
nohup ~/rp_persona/scripts/serve_lora.sh 0 8001 imp=$A/dpo_implicit exp=$A/dpo_explicit rft=$A/sft_rft > $R/serve_lora.log 2>&1 &
until curl -s http://localhost:8001/v1/models | grep -q rft; do sleep 10; done
echo "lora server up $(date)"
for ARM in q8 imp exp rft; do
  for DEP in 2 20; do
    $PY e0d_mechanism.py --policy_name $ARM --policy_label $ARM --depth $DEP --conds full --n 4 \
      --probe_types false_premise,true_premise,none,meta_ai,pressure,assistant_task \
      --out $R/e1/eval_${ARM}_d$DEP.jsonl > $R/e1_eval_${ARM}_d$DEP.log 2>&1 || { echo "eval $ARM d$DEP failed"; exit 1; }
  done
done
echo "eval gen done $(date)"
$PY e0c_judge.py --inp $R/e1/eval_*_d*.jsonl > $R/e1_judge.log 2>&1 || { echo "judge failed"; exit 1; }
echo "ALL DONE $(date)"
