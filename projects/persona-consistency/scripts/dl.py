import sys
from huggingface_hub import snapshot_download, hf_hub_download
what = sys.argv[1]
if what == "herdata":
    print(hf_hub_download('ChengyuDu0123/HER-Dataset', 'data/HER_dataset_sft_multi_turn.jsonl', repo_type='dataset'))
else:
    print(snapshot_download(what, max_workers=16))
