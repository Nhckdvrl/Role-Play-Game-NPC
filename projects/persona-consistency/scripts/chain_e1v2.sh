#!/bin/bash
# E1 v2 (fixed prefill boundary): retrain arms on GPU0/GPU1, serve adapters, evaluate on fixed histories, judge.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; D=~/rp_persona/data/e1_v2; A=/tmp/xiang_rp/e1v2; mkdir -p $A
gpu1() {
  CUDA_VISIBLE_DEVICES=1 $PY e0g2_feats.py > $R/e0g2_feats.log 2>&1 && $PY analyze_e0g2.py --out results/e0g2_minimalpair_q8.txt > $R/e0g2_analysis.log 2>&1
  echo "e0g2 done $(date)"
  CUDA_VISIBLE_DEVICES=1 $PY e1_train.py --algo dpo --data $D/dpo_explicit.jsonl --out $A/exp > $R/e1v2_train_exp.log 2>&1
  echo "exp_v2 trained $(date)"
  CUDA_VISIBLE_DEVICES=1 $PY e1_train.py --algo dpo --lr 5e-5 --data $D/dpo_implicit_all.jsonl --out $A/impall > $R/e1v2_train_impall.log 2>&1
  echo "impall_v2 trained $(date)"
}
gpu0() {
  until grep -qE "eval gen done|failed" $R/chain_e1.log; do sleep 30; done
  pkill -f "served-model-name q8 "; sleep 20
  CUDA_VISIBLE_DEVICES=0 $PY e1_train.py --algo dpo --data $D/dpo_implicit.jsonl --out $A/imp > $R/e1v2_train_imp.log 2>&1
  echo "imp_v2 trained $(date)"
  CUDA_VISIBLE_DEVICES=0 $PY e1_train.py --algo sft --data $D/sft_rft.jsonl --out $A/rft > $R/e1v2_train_rft.log 2>&1
  echo "rft_v2 trained $(date)"
}
gpu1 & P1=$!
gpu0 & P0=$!
wait $P0 $P1
nohup ~/rp_persona/scripts/serve_lora.sh 0,1 8001 imp2=$A/imp exp2=$A/exp rft2=$A/rft impall2=$A/impall > $R/serve_lora_v2.log 2>&1 &
until curl -s http://localhost:8001/v1/models | grep -q impall2; do sleep 10; done
echo "lora v2 server up $(date)"
for ARM in imp2 exp2 rft2 impall2; do
  for DEP in 2 20; do
    $PY e0d_mechanism.py --policy_name $ARM --policy_label $ARM --depth $DEP --conds full --n 4 \
      --probe_types false_premise,true_premise,none,meta_ai,pressure,assistant_task \
      --out $R/e1/evalv2_${ARM}_d$DEP.jsonl > $R/e1v2_eval_${ARM}_d$DEP.log 2>&1 || { echo "eval $ARM d$DEP failed"; exit 1; }
  done
done
echo "v2 eval gen done $(date)"
until grep -qE "ALL DONE|failed" $R/chain_e1.log; do sleep 30; done
$PY e0c_judge.py --inp $R/e1/evalv2_*_d*.jsonl > $R/e1v2_judge.log 2>&1 || { echo "judge failed"; exit 1; }
echo "ALL DONE $(date)"
