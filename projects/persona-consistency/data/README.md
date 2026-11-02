# 精选数据

由 [../exp/export_curated_data.py](../exp/export_curated_data.py) 从集群上的 `~/rp_persona/` 导出。只包含 ID、简短的生成探针、标签与分数，**不含**生成文本全文和上游数据集原文。

| 文件 | 内容 | 来源 |
| --- | --- | --- |
| `splits.jsonl` | 评测 48 段 / 训练对话的 ID、作品名、角色名（作品与角色不重叠） | HER 多轮 SFT 数据（`ChengyuDu0123/HER-Dataset`），按 ID 重建原文 |
| `probes_closed_loop.jsonl` | 每段评测对话的探针：错误说法（含错误要点与真相）、真实说法、施压、世界外任务、AI 身份质问 | Qwen3-32B 依据设定生成 |
| `probes_full.jsonl` | 上者的超集：有效性标记（`false_valid` 等）、留出风格（引导式提问、改写措辞的 AI 质问）、普通提问、出戏探针 | 同上；出戏探针为模板 |
| `minimal_pairs.jsonl` | 最小对照对：设定中逐字出现的值、替代值、包含原值的台词；反事实设定 = 对原设定做精确字符串替换 | Qwen3-32B 提议并校验 |
| `audit/human_blind_labels.jsonl` | 48 条闭环“错误说法”回复的人工盲标（A 接受 / C 纠正 / D 回避 / N 语境中不算明确错误说法） | 2026-11-02 人工审计 |
| `labels/closed_loop_*_judge.jsonl.gz` | 各轮闭环（base、三次独立重复、各训练轮次、Mistral 模拟器）的逐条判分标签，Qwen3-32B 与 Mistral 两套 | `exp/e0c_judge.py` |
| `labels/fixed_history.jsonl.gz`、`heldout_benign.jsonl.gz`、`p1_selectivity.jsonl.gz`、`e0d_mechanism.jsonl.gz` | 固定历史评测、留出风格与普通提问、出戏选择性、机制实验的逐条标签 | 同上 |
| `coser_scene_scores.jsonl` | CoSER GCA 200 个场景、各模型的四维分数与轮数 | `exp/run_coser_gca.py`（Qwen3-32B 评审） |

**注意**：`labels/` 中的闭环标签来自原始的整体式裁判。2026-11-02 的审计发现它会把坚定的语气当成纠正，对“接受错误说法”的召回率很低，所以这些标签应结合审计结果解读，正在用 `exp/claim_judge.py` 重估。
