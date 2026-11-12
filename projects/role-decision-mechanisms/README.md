# role-decision-mechanisms：角色条件决策的内部机制（新方向，2026-11-11 开始）

> 状态（2026-11-12 下午）：阅读、行为、机制、干预、独立测试集复核、测量效度、角色扮演训练模型对比都已完成第一轮。第二轮补充了对话格式、冲突、身份（职业与经历）、价值的独立测试，训练迁移与身份的机制，以及真实小说上的外部效度（LifeChoice 端任务、长文本反事实插入）和由机制推出的探针门控（M8，自然叙事中无效）。**阶段总结见 [SUMMARY.md](SUMMARY.md)**，全部实验见 [EXPERIMENTS_LOG.md](EXPERIMENTS_LOG.md)，数据划分见 [DATA.md](DATA.md)，领域层面的计划见 [PLAN.md](PLAN.md)。

核心问题：LLM 能正确说出角色知道什么、相信什么、遵守什么原则，为什么在以角色身份做决定时却不一定照做？失败时模型内部发生了什么？能否选择性干预？

| 文件 | 内容 |
| --- | --- |
| [DIRECTION.md](DIRECTION.md) | 用户与 Gemini 讨论得出的研究方向说明（原文存档，2026-11-11） |
| [LITERATURE_SYNTHESIS.md](LITERATURE_SYNTHESIS.md) | 精读后的整体认知：已知、未知、对方向说明的修正与风险 |
| [reading_notes/](reading_notes/) | 逐篇精读笔记（英文） |
| [SUMMARY.md](SUMMARY.md) | 阶段总结（含证据等级） |
| [EXPERIMENTS_LOG.md](EXPERIMENTS_LOG.md) | 全部实验记录 |
| [DATA.md](DATA.md) | 数据来源、版本、dev/test 划分与已知问题 |
| [PLAN.md](PLAN.md) | 领域层面的问题与阶段计划 |
| [src/](src/README.md) | 场景族、提示构造、打分、机制实验与分析脚本（按用途分组的索引见 src/README.md） |
| [results/](results/) | 汇总结果 |

论文全文与提取文本放在集群 `~/rp_mech/`（不入库），下载清单见 `~/rp_mech/list.tsv`。逐条提示与输出也在 `~/rp_mech/` 下：

| 目录 | 内容 |
| --- | --- |
| `s1/`–`s12/` | 开发数据（dev）上的各切片 |
| `test/`、`test_dlg/`、`test_conf/` | T 集及其对话格式、冲突派生集；`test/methods/` 为冻结方法 |
| `identity/`、`values_test/` | 身份切片（dev/test）与价值独立测试集 |
| `mech/`、`identity/mech/` | 机制实验的输出 |
| `sft/` | LoRA 训练数据、适配器与评测 |
| `scale/`、`scale2/` | Qwen3 规模对比（dev；T 派生集上的 14B/32B） |
| `capab/` | 训练副作用检查（MMLU、ARC） |
| `lifechoice/`、`lc_inject/`、`data_ext/lifechoice/` | LifeChoice 端任务与真实小说长文本插入（E2、E3） |
| `probe_gate/` | 两遍归属探针门控（M8） |
| `rpmodels/`、`freegen/`、`heart/`、`think/` | 角色扮演训练模型、自由生成、HEART、思考模式 |

与其他工作的边界：
- `projects/reason-sensitive-roleplay`：研究多轮对话中依据证据改变决定的训练方法；本项目研究单步角色条件决策的内部机制，不做 RL 训练。
- `discussions/2026-11-topic-selection`：上一轮选题中已放弃 Curse of Knowledge 行为方向（拥挤）与 RoleCDE 默认倾向方向；本项目复用其数据与发现，但问题换成“机制”。
