# 2026-11 选题讨论（persona-consistency 归档之后）

> 用途：完整记录新选题的讨论过程，供**未参与讨论的 agent 或人**读完后给出旁观的、全局性的反馈，而不是顺着讨论各方的思路走。请特别留意各方前后修正过的说法，以及仍未解决的分歧。

## 参与方

- **用户**：项目负责人，做最终决定。
- **Claude**：本地研究 agent（Claude Code），负责文献核查、评估和方案设计。
- **Gemini**：用户转述的另一方意见。根据仓库中的 [DUAL_MODEL_WEAKNESSES.md](../../DUAL_MODEL_WEAKNESSES.md)，它容易过度乐观、把局部数字戏剧化。
- **GPT-6 调研稿**：用户提供的领域全景调研（66 项文献），作为背景材料。

## 文件

| 文件 | 内容 |
| --- | --- |
| [SUMMARY.md](SUMMARY.md) | **选题阶段总结（已结束）**：时间线、实验发现、领域收获、教训、资产位置 |
| [explorations/](explorations/README.md) | 两组探索实验的代码与结果汇总（角色声音；演员模型默认倾向 E1–E6） |
| [01_ROUND_LOG.md](01_ROUND_LOG.md) | 按轮次记录：每轮各方的主要主张、被纠正的事实、达成的共识 |
| [02_LITERATURE_VERIFIED.md](02_LITERATURE_VERIFIED.md) | 讨论中核查过的论文：读到什么程度（全文、摘要），方法、评测与裁判细节，与本讨论的关系 |
| [03_CANDIDATES.md](03_CANDIDATES.md) | 各候选方向的评估与当前状态；首选方向的当前设计，区分“已确立的事实”和“尚待证实的假设” |
| [04_OPEN_QUESTIONS.md](04_OPEN_QUESTIONS.md) | 未解决的问题与分歧，特别希望旁观者评估的点 |
| [09_FIELD_SYNTHESIS.md](09_FIELD_SYNTHESIS.md) | 第 12 轮：停下实验，系统阅读约 45 篇全文后的领域综合（共识、争议、开放问题）；逐篇笔记在 [reading_notes/](reading_notes/) |
| [08_NEW_DIRECTION.md](08_NEW_DIRECTION.md) | 第 10 轮：用户认为 Z1 拥挤，改找不拥挤的方向；候选 V“角色的声音”（个人风格保持与角色间区分）及其可行性、测量灵敏度测试与风险 |
| [07_FIELD_AND_FEASIBILITY.md](07_FIELD_AND_FEASIBILITY.md) | 第 9 轮：领域重要性、候选方向的可行性对比；Z1 的数据清单（实际下载统计）、零 GPU 试分析、测量有效性、baseline、API 与计算量、风险 |
| [06_EXPLORATION_ZONES.md](06_EXPLORATION_ZONES.md) | 第 8 轮：工作方式改为“先选探索地带、再用实验凝练 idea”；核查 Gemini 的五个地带；推荐地带与第一批实验草案 |
| [05_ROADMAP_SCREEN.md](05_ROADMAP_SCREEN.md) | 第 7 轮：用固定的七条标准，对 ROADMAP 全部 31 个证据区域做系统筛选；最接近通过的两项补读了原文 |

## 背景

上一个子题 [persona-consistency](../../projects/persona-consistency/SUMMARY.md) 于 2026-11-02 归档。根本原因是：整个项目使用的 LLM 裁判（Qwen3-32B 非思考模式）未经人工验证，会把角色坚定的语气当作“纠正”，漏掉了绝大多数应被判为失败的回复。由此产生的讨论原则：

1. 任何裁判或奖励模型在使用前，都必须先用人工标注验证；
2. 优先选择有结构化真值、或能做到不依赖裁判的测量；
3. **不赌假设**（用户 2026-11-02 明确提出）：研究计划应建立在已确立的事实上，每个关键环节都应有独立的先验证据。论文的核心贡献，不应押在某一个尚未证实的现象上；
4. 只做纯分析、不给出新方法（训练或训练无关），投稿前景有限（用户 2026-11-02 提出）。

## 当前状态（2026-11-02，已结束）

- **选题阶段结束，未立项**。用户在第 15 轮叫停最后一个探索方向，要求删除检查点并归档。总结见 [SUMMARY.md](SUMMARY.md)。
- 可复用的成果：领域综合（[09](09_FIELD_SYNTHESIS.md)）与逐篇笔记（[reading_notes/](reading_notes/)）、ROADMAP 系统筛选（[05](05_ROADMAP_SCREEN.md)）、数据可行性核查（[07](07_FIELD_AND_FEASIBILITY.md)）、两组实验的代码与结果（[explorations/](explorations/README.md)）。
