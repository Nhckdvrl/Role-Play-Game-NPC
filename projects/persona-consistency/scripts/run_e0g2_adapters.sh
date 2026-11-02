#!/bin/bash
# Minimal-pair conflict readability under trained adapters (does training raise late-layer readability?).
PY=~/miniconda3/envs/verl-clean/bin/python
cd /home/xiang/Role-Play-Game-NPC/exp
R=~/rp_persona/runs
(
  until grep -q "x2 done" $R/run_e0i_dose.log; do sleep 30; done
  CUDA_VISIBLE_DEVICES=0 $PY e0g2_feats.py --adapter /tmp/xiang_rp/e1v2/impall --out $R/e0g/feats2_impall2.npz > $R/e0g2_impall2.log 2>&1
  $PY analyze_e0g2.py --feats $R/e0g/feats2_impall2.npz --out results/e0g2_minimalpair_impall2.txt >> $R/e0g2_impall2.log 2>&1
) &
(
  until grep -q "x4 done" $R/run_e0i_dose.log; do sleep 30; done
  CUDA_VISIBLE_DEVICES=1 $PY e0g2_feats.py --adapter /tmp/xiang_rp/e1v3/ddpo --out $R/e0g/feats2_ddpo.npz > $R/e0g2_ddpo.log 2>&1
  $PY analyze_e0g2.py --feats $R/e0g/feats2_ddpo.npz --out results/e0g2_minimalpair_ddpo.txt >> $R/e0g2_ddpo.log 2>&1
) &
wait
echo "E0G2 ADAPTERS DONE $(date)"
