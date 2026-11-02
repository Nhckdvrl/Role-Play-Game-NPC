#!/bin/bash
PY=/home/xiang/miniconda3/envs/verl-clean/bin/python
S=$HOME/rp_prior/src; O=$HOME/rp_prior/results; mkdir -p $O
cd $S
$PY -I analyze_e1.py > $O/e1.txt 2>&1
$PY -I analyze_e2.py > $O/e2.txt 2>&1
$PY -I analyze_frames.py e3 recognize_v predict_v enact_v > $O/e3.txt 2>&1
$PY -I analyze_frames.py e4 oneline+value nopers+value full+value full+value2 > $O/e4.txt 2>&1
$PY -I analyze_frames.py e5 oneline+value oneline+filler+value oneline+value+filler otherfull+value full+value value+full > $O/e5.txt 2>&1
$PY -I analyze_e6.py e6 > $O/e6.txt 2>&1
$PY -I wording.py > $O/e1_wording.txt 2>&1
echo done
