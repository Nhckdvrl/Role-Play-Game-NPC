#!/bin/bash
# Qwen3.5-9B replication of the whole study on fvcrc20 (4x RTX PRO 6000; fgvd env = transformers 5 + vLLM 0.23 for serving
# and training; client scripts in verl-clean). Stages: S1 baseline closed loop + round-1 data | S2 round-1 DPO (implicit-all)
# -> merged r1 | S3 round-2 balanced data from r1 (7 probes + strict-verified OOC) | S4 round-2 DPO -> merged r2 | S5 eval.
set -u
PY=~/miniconda3/envs/verl-clean/bin/python; FP=~/miniconda3/envs/fgvd/bin/python; TR=~/miniconda3/envs/fgvd/bin/torchrun
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs; D=~/rp_persona/data/q35; L=/tmp/xiang_rp/models; Q=$L/Qwen3.5-9B; W=/tmp/xiang_rp/q35
mkdir -p $D $W $R/q35
H=~/rp_persona/data/e0c_probes_heldout.jsonl; O=~/rp_persona/data/e0c_probes_ooc.jsonl
serve() {  # model gpus tp port name util
  CUDA_VISIBLE_DEVICES=$2 VLLM_USE_FLASHINFER_SAMPLER=0 nohup $FP -m vllm.entrypoints.openai.api_server --model $1 --served-model-name $5 --tensor-parallel-size $3 \
    --port $4 --max-model-len 20480 --gpu-memory-utilization $6 --limit-mm-per-prompt '{"image":0,"video":0}' > $R/q35/serve_$5.log 2>&1 &
}
up() { until curl -s http://localhost:$1/v1/models | grep -q "\"$2\""; do grep -q " ERROR " $R/q35/serve_$2.log 2>/dev/null && { echo "serve $2 failed"; exit 1; }; sleep 15; done; echo "$2 up $(date)"; }
kill_name() { for p in $(pgrep -f "[s]erved-model-name $1 "); do kill $p; done; }
free_gpus() { sleep 10; for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i $1); do kill $p; done; sleep 10; }

# ---------- S1
CUDA_VISIBLE_DEVICES=2,3 VLLM_USE_FLASHINFER_SAMPLER=0 nohup $FP -m vllm.entrypoints.openai.api_server --model $L/Qwen3-32B --served-model-name q32 --tensor-parallel-size 2 \
  --port 8000 --max-model-len 20480 --gpu-memory-utilization 0.90 > $R/q35/serve_q32.log 2>&1 &
serve $Q 0 1 8020 q35 0.90
up 8000 q32; up 8020 q35
U="--policy_url http://localhost:8020/v1 --policy_name q35 --policy_tok $Q"
$PY e0c_stress.py --tag q35her --mode her $U --sim_url http://localhost:8000/v1 > $R/q35/e0c_base.log 2>&1 &
P1=$!
$PY e1_data.py $U --n_convs 128 --k_def 5 --k_sc 0 --out $R/q35/r1_data.jsonl --convs_out $D/train_convs_r1.jsonl > $R/q35/r1_data.log 2>&1 || { echo "S1 r1 data failed"; exit 1; }
wait $P1 || { echo "S1 closed loop failed"; exit 1; }
echo "S1 done $(date)"
$PY e0c_judge.py --url http://localhost:8000/v1 --probes ~/rp_persona/data/e0c_probes_v1.jsonl --inp $R/e0c/e0c_q35her.jsonl > $R/q35/judge_base.log 2>&1 &
P1=$!
# ---------- S2
$PY e1_pairs.py --data $R/q35/r1_data.jsonl --out_dir $D/r1 --tok $Q > $R/q35/r1_pairs.log 2>&1; tail -3 $R/q35/r1_pairs.log
kill_name q35; free_gpus 0,1
CUDA_VISIBLE_DEVICES=0,1 $TR --nproc_per_node 2 --master_port 29531 e1_train_lite.py --model $Q --data $D/r1/dpo_implicit_all.jsonl \
  --out $W/r1 --lr 5e-5 --epochs 2 --grad_acc 8 --merge > $R/q35/r1_train.log 2>&1 || { echo "S2 train failed"; exit 1; }
echo "S2 r1 trained $(date)"
wait $P1
# ---------- S3
serve $W/r1/merged 0 1 8021 q35r1 0.90
up 8021 q35r1
U1="--policy_url http://localhost:8021/v1 --policy_name q35r1 --policy_tok $Q"
$PY e1v5_data.py $U1 --n_convs 96 --out $R/q35/r2_data.jsonl --convs_out $D/train_convs_r2.jsonl > $R/q35/r2_data.log 2>&1 || { echo "S3 r2 data failed"; exit 1; }
$PY e1r4_ooc_data.py --src $R/q35/r2_data.jsonl --out $R/q35/r2_ooc_data.jsonl --train_convs $D/train_convs_r2.jsonl \
  --policy_url http://localhost:8021/v1 --policy_name q35r1 --policy_tok $Q > $R/q35/r2_ooc.log 2>&1 || { echo "S3 ooc data failed"; exit 1; }
$PY e1v5_pairs.py --data $R/q35/r2_data.jsonl --out $D/r2/dpo_main.jsonl --tok $Q > $R/q35/r2_pairs.log 2>&1
$PY e1v5_pairs.py --data $R/q35/r2_ooc_data.jsonl --out $D/r2/dpo_ooc.jsonl --tok $Q >> $R/q35/r2_pairs.log 2>&1
$PY verify_ooc_pairs.py --inp $D/r2/dpo_ooc.jsonl --out $D/r2/dpo_ooc_verified.jsonl >> $R/q35/r2_pairs.log 2>&1
cat $D/r2/dpo_main.jsonl $D/r2/dpo_ooc_verified.jsonl $D/r2/dpo_ooc_verified.jsonl > $D/r2/dpo_r2.jsonl
grep -E "pairs|kept|fail rate" $R/q35/r2_pairs.log; wc -l $D/r2/dpo_r2.jsonl
echo "S3 done $(date)"
# ---------- S4
kill_name q35r1; free_gpus 0,1
CUDA_VISIBLE_DEVICES=0,1 $TR --nproc_per_node 2 --master_port 29532 e1_train_lite.py --model $W/r1/merged --data $D/r2/dpo_r2.jsonl \
  --out $W/r2 --lr 5e-5 --epochs 2 --grad_acc 8 --merge > $R/q35/r2_train.log 2>&1 || { echo "S4 train failed"; exit 1; }
echo "S4 r2 trained $(date)"
# ---------- S5
serve $Q 0 1 8020 q35 0.90
serve $W/r2/merged 1 1 8022 q35r2 0.90
up 8020 q35; up 8022 q35r2
U2="--policy_url http://localhost:8022/v1 --policy_name q35r2 --policy_tok $Q"
$PY e0c_stress.py --tag q35r2her --mode her $U2 --sim_url http://localhost:8000/v1 > $R/q35/e0c_r2.log 2>&1 &
PA=$!
for m in "q35 8020" "q35r2 8022"; do set -- $m
  UU="--policy_url http://localhost:$2/v1 --policy_name $1 --policy_tok $Q"
  $PY e0d_mechanism.py --probes $H $UU --policy_label $1 --depth 20 --conds full --n 4 --probe_types false_q,meta_p1,meta_p2,meta_p3,benign_q --out $R/e1/heldout_$1_d20.jsonl > $R/q35/heldout_$1.log 2>&1
  $PY e0d_mechanism.py $UU --policy_label $1 --depth 20 --conds full --n 8 --sample_offset 100 --probe_types false_premise,meta_ai,true_premise,none --out $R/e1/evalv6_$1_d20.jsonl > $R/q35/eval_$1.log 2>&1
  $PY e0d_mechanism.py --probes $O $UU --policy_label $1 --depth 20 --conds full --n 4 --sample_offset 200 --probe_types meta_ai,ooc_ai_1,ooc_ai_2,ooc_ai_3,ooc_req_1,ooc_req_2 --out $R/e1/p1_$1_d20.jsonl > $R/q35/p1_$1.log 2>&1
  $PY gen_apc_server.py --url http://localhost:$2/v1 --models $1 --tok $Q > $R/q35/apc_gen_$1.log 2>&1
done
wait $PA || { echo "S5 closed loop failed"; exit 1; }
echo "S5 gen done $(date)"
$PY e0c_judge.py --url http://localhost:8000/v1 --probes ~/rp_persona/data/e0c_probes_v1.jsonl --inp $R/e0c/e0c_q35r2her.jsonl > $R/q35/judge_r2.log 2>&1
for m in q35 q35r2; do
  $PY e0c_judge.py --url http://localhost:8000/v1 --probes $H --inp $R/e1/heldout_${m}_d20.jsonl >> $R/q35/judge_r2.log 2>&1
  $PY e0c_judge.py --url http://localhost:8000/v1 --inp $R/e1/evalv6_${m}_d20.jsonl >> $R/q35/judge_r2.log 2>&1
  $PY e0c_judge.py --url http://localhost:8000/v1 --probes $O --inp $R/e1/p1_${m}_d20.jsonl >> $R/q35/judge_r2.log 2>&1
done
$PY judge_hostility.py --tags q35her,q35r2her > $R/q35/hostility.log 2>&1
RT='{"q32": "http://localhost:8000/v1", "q35": "http://localhost:8020/v1", "q35r2": "http://localhost:8022/v1"}'
$PY run_coser_gca.py --actor q35 --routes "$RT" --workers 40 > $R/q35/coser_q35.log 2>&1 &
PC=$!
$PY run_coser_gca.py --actor q35r2 --routes "$RT" --workers 40 > $R/q35/coser_q35r2.log 2>&1
wait $PC
kill_name q35; kill_name q35r2; free_gpus 0,1
for m in q35 q35r2; do CUDA_VISIBLE_DEVICES=0 $PY score_apc.py --gen $R/e0a/gen_srv_$m.jsonl > $R/q35/apc_score_$m.log 2>&1; done
echo "ALL DONE $(date)"
