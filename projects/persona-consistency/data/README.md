# 精选数据

由 [../exp/export_curated_data.py](../exp/export_curated_data.py) 从集群上的 `~/rp_persona/` 导出。只包含 ID、简短的生成探针和标签，**不含**生成文本全文和上游数据集原文。

| 文件 | 内容 | 来源 |
| --- | --- | --- |
| `splits.jsonl` | 评测 48 段 / 训练对话的 ID、作品名、角色名（作品与角色不重叠） | HER 多轮 SFT 数据（`ChengyuDu0123/HER-Dataset`），按 ID 重建原文 |
| `probes_closed_loop.jsonl` | 闭环实验使用的探针：错误说法（含错误要点与真相）、真实说法、施压、世界外任务、AI 身份质问 | Qwen3-32B 依据设定生成 |
| `probes_full.jsonl` | 上者的超集：有效性标记、留出风格、普通提问、出戏探针 | 同上；出戏探针为模板 |
| `minimal_pairs.jsonl` | 最小对照对：设定中逐字出现的值、替代值、包含原值的台词；反事实设定 = 对原设定做精确字符串替换 | Qwen3-32B 提议并校验 |
| `audit/human_blind_labels_set1.jsonl` | 48 条 base 闭环“错误说法”回复的人工盲标（第 2 / 20 轮） | 2026-11-02 人工审计 |
| `audit/human_blind_labels_set2.jsonl` | 40 条第 20 轮回复的人工盲标，来自 base、r2′-2ep、r2″（隐藏来源） | 同上 |
| `labels/false_premise_step5_judge.jsonl.gz` | 经人工验证的裁判（step-5-preview，原评分标准）对错误说法探针的标签：base 三次闭环与 r2′-2ep | `exp/rejudge_step5.py` |

人工标签含义：A 接受错误说法 / C 纠正 / D 回避 / N 语境中不算明确的错误说法。

**审计发现原裁判（Qwen3-32B 非思考模式）以及 Mistral-Small 交叉裁判的标签不可靠**：它们会漏掉大多数“接受”。因此这里不导出它们。
