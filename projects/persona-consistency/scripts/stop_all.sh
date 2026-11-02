#!/bin/bash
# Kill this project's processes on the current node by PID (never by a pattern that could match the calling shell).
ME=$$; PARENT=$PPID
for pid in $(ps -eo pid=,args= | awk '/vllm.entrypoints|VLLM::|chain_q35|chain_panel|chain_r2pp|e0c_stress.py|e1_data.py|e0m_grounding.py|e0m_judge.py|rejudge_step5.py|run_p3_when_free|e1_train/ && !/awk/ {print $1}'); do
  [ "$pid" = "$ME" ] || [ "$pid" = "$PARENT" ] || kill $pid 2>/dev/null
done
sleep 15
for pid in $(ps -eo pid=,args= | awk '/vllm.entrypoints|VLLM::/ && !/awk/ {print $1}'); do kill -9 $pid 2>/dev/null; done
nvidia-smi --query-gpu=index,memory.used --format=csv,noheader
