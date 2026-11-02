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
| [01_ROUND_LOG.md](01_ROUND_LOG.md) | 按轮次记录：每轮各方的主要主张、被纠正的事实、达成的共识 |
| [02_LITERATURE_VERIFIED.md](02_LITERATURE_VERIFIED.md) | 讨论中核查过的论文：读到什么程度（全文、摘要），方法、评测与裁判细节，与本讨论的关系 |
| [03_CANDIDATES.md](03_CANDIDATES.md) | 各候选方向的评估与当前状态；首选方向的当前设计，区分“已确立的事实”和“尚待证实的假设” |
| [04_OPEN_QUESTIONS.md](04_OPEN_QUESTIONS.md) | 未解决的问题与分歧，特别希望旁观者评估的点 |
| [06_EXPLORATION_ZONES.md](06_EXPLORATION_ZONES.md) | 第 8 轮：工作方式改为“先选探索地带、再用实验凝练 idea”；核查 Gemini 的五个地带；推荐地带与第一批实验草案 |
| [05_ROADMAP_SCREEN.md](05_ROADMAP_SCREEN.md) | 第 7 轮：用固定的七条标准，对 ROADMAP 全部 31 个证据区域做系统筛选；最接近通过的两项补读了原文 |

## 背景

上一个子题 [persona-consistency](../../projects/persona-consistency/SUMMARY.md) 于 2026-11-02 归档。根本原因是：整个项目使用的 LLM 裁判（Qwen3-32B 非思考模式）未经人工验证，会把角色坚定的语气当作“纠正”，漏掉了绝大多数应被判为失败的回复。由此产生的讨论原则：

1. 任何裁判或奖励模型在使用前，都必须先用人工标注验证；
2. 优先选择有结构化真值、或能做到不依赖裁判的测量；
3. **不赌假设**（用户 2026-11-02 明确提出）：研究计划应建立在已确立的事实上，每个关键环节都应有独立的先验证据。论文的核心贡献，不应押在某一个尚未证实的现象上；
4. 只做纯分析、不给出新方法（训练或训练无关），投稿前景有限（用户 2026-11-02 提出）。

## 当前状态（2026-11-02，第 8 轮后）

- **工作方式调整**（用户第 8 轮）：不再寻找“一次跑通”的完整 idea，而是先选一片宽广的探索地带，用高信息量实验凝练 insight。测量可靠（C2）和不与其他子项目重叠（C5）仍是硬约束。
- **推荐地带**：“角色的认知状态与模型全知的分离”（Character Epistemics），合并了 Gemini 的地带 2、第 7 轮的 S3′ 和无条件的秘密。条件披露留给 reason-sensitive-roleplay。锚点现象为 Curse of Knowledge 与 SimpleToM；主测量是孪生场景加规则评分，不需要 LLM 裁判。见 [06_EXPLORATION_ZONES.md](06_EXPLORATION_ZONES.md)。
- 第一批实验（X0–X5）只是草案，**尚未执行**。是否进入该地带、是否从 X0 开始，由用户决定。
- 第 7 轮的系统筛选见 [05_ROADMAP_SCREEN.md](05_ROADMAP_SCREEN.md)；C、2b、G1、G2 仍为不推荐。
