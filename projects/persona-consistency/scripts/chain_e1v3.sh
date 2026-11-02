#!/bin/bash
# E1 v3: lr ablation (imp_lr5e5), context-distillation arms, explicit v3; robust eval at depth 20 on the base_supp seeds.
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; A=/tmp/xiang_rp/e1v3; mkdir -p $A
gpu0() {
  until [ -f $R/e1b_gen_done ] && ! nvidia-smi --query-compute-apps=pid --format=csv,noheader -i 0 | grep -q .; do sleep 20; done
  CUDA_VISIBLE_DEVICES=0 $PY e1_train.py --algo dpo --lr 5e-5 --data ~/rp_persona/data/e1_v2/dpo_implicit.jsonl --out $A/imp5 > $R/e1v3_train_imp5.log 2>&1
  echo "imp5 trained $(date)"
  until grep -q "E1B DATA DONE" $R/run_e1b.log; do sleep 20; done
  [ -f ~/rp_persona/data/e1b/distill_dpo.jsonl ] || $PY e1b_pairs.py > $R/e1b_pairs.log 2>&1
  CUDA_VISIBLE_DEVICES=0 $PY e1_train.py --algo dpo --lr 5e-5 --data ~/rp_persona/data/e1b/distill_dpo.jsonl --out $A/ddpo > $R/e1v3_train_ddpo.log 2>&1
  echo "ddpo trained $(date)"
}
gpu1() {
  until grep -q "exp_v3 trained" $R/train_exp3.log; do sleep 20; done
  until grep -q "E1B DATA DONE" $R/run_e1b.log; do sleep 20; done
  sleep 5; [ -f ~/rp_persona/data/e1b/distill_sft.jsonl ] || $PY e1b_pairs.py > $R/e1b_pairs.log 2>&1
  sleep 5
  CUDA_VISIBLE_DEVICES=1 $PY e1_train.py --algo sft --lr 5e-5 --epochs 1 --data ~/rp_persona/data/e1b/distill_sft.jsonl --out $A/dsft > $R/e1v3_train_dsft.log 2>&1
  echo "dsft trained $(date)"
}
gpu0 & P0=$!; gpu1 & P1=$!
wait $P0 $P1
cat $R/e1b_pairs.log
TP=2 nohup ~/rp_persona/scripts/serve_lora.sh 0,1 8001 impall2=/tmp/xiang_rp/e1v2/impall exp3=$A/exp imp5=$A/imp5 dsft=$A/dsft ddpo=$A/ddpo > $R/serve_lora_v3.log 2>&1 &
until curl -s http://localhost:8001/v1/models | grep -q ddpo; do sleep 10; done
echo "lora v3 server up $(date)"
for ARM in impall2 exp3 imp5 dsft ddpo; do
  $PY e0d_mechanism.py --policy_name $ARM --policy_label $ARM --depth 20 --conds full --n 8 --sample_offset 100 \
    --probe_types false_premise,meta_ai,true_premise,none --out $R/e1/evalv3_${ARM}_d20.jsonl > $R/e1v3_eval_${ARM}.log 2>&1 || { echo "eval $ARM failed"; exit 1; }
done
echo "v3 eval gen done $(date)"
$PY e0c_judge.py --inp $R/e1/evalv3_*_d20.jsonl > $R/e1v3_judge.log 2>&1 || { echo "judge failed"; exit 1; }
echo "ALL DONE $(date)"
