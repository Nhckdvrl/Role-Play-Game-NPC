# 子项目：长对话角色扮演中的人设一致性

> 所属总项目：[Role-Play-Game-NPC](../../README.md)。本目录是总项目下的一个子题，代码、数据、实验记录和文档都在这里自成一体。

## 研究问题

纯文本单轮与多轮角色对话中的 **Persona Consistency & Character Fidelity**：浅层扮演，以及多轮对话中的人设消退和出戏。技术视角为 **A：强化学习与角色推理**、**B：Persona Probes 与激活控制**。题目定义见 [RESEARCH_IDEAS.md](RESEARCH_IDEAS.md)。

实验目前聚焦的现象是**长对话中的顺从漂移**：故事场景里，随着对话变长，角色越来越容易在角色口吻之内顺着对方的说法走，例如接受关于自己的错误说法、在施压下放弃特质、执行故事世界外的任务。

## 当前状态（2026-11-02）

| 层面 | 目前的结论 | 证据强度与未解决的问题 |
| --- | --- | --- |
| 现象 | Qwen3-8B 第 2→20 轮，接受关于自己的错误说法从 0.06 升到 0.27；Qwen3-14B、HER-32B 也有；换 Mistral 作模拟器或裁判后仍然存在 | **测量效度正在复核。** 48 条盲样本的人工审计发现：原裁判会把坚定、有对抗性的**语气**当成“纠正”，漏掉了大部分明确的接受（12 条里只抓到 2 条）；约三分之一的探针在语境里并不是明确的错误说法。绝对失败率被低估，训练收益可能被高估。见 [docs/SYNTHESIS_2026-11-02.md](docs/SYNTHESIS_2026-11-02.md) |
| 机制 | 不是遗忘而是没用上（场外读出 94%，明确核对可压到 0.03）；顺从发生在越来越入戏的状态下，表征上**远离**助手端（与 Persistent Personas 的“回退助手”设置不同） | 单模型；知名角色的预训练记忆是未排除的混杂 |
| 方法 | 在模型自己的闭环轨迹上做第二轮在线 DPO，偏好数据同时覆盖“该坚持”和“该让步”两类：自建指标上核心失败接近清零，APC 不降，CoSER 不退化（+1.9 到 +2.5） | 依赖上面那个有偏差的裁判；CoSER 的评审与训练标签同为 Qwen3-32B；只训练了 Qwen3-8B（Qwen3.5-9B 复现进行中） |

正在进行：
1. 用聚焦内容、先引用证据再判断的新裁判（[exp/claim_judge.py](exp/claim_judge.py)）重估全部数据，并用人工标注检验它；
2. 真相完全确定的 2×2 最小对照探针 × 深度 × 15 个模型的面板（[exp/e0m_grounding.py](exp/e0m_grounding.py)），其中包含 HER-32B 与其底座 Qwen3-32B 这一对角色扮演训练前后的对照；
3. Qwen3.5-9B 的完整复现。

## 文档

| 文件 | 内容 |
| --- | --- |
| [docs/SYNTHESIS_2026-11-02.md](docs/SYNTHESIS_2026-11-02.md) | **最新阶段复盘**：领域画像、现有结论的真实分量、按信息量排序的下一步 |
| [EXPERIMENTS_LOG.md](EXPERIMENTS_LOG.md) | 按时间顺序的完整实验记录（E0-A … E0-M、E1 各轮、外部基准），顶部有结论速览 |
| [RESEARCH_IDEAS.md](RESEARCH_IDEAS.md) | 子题定义 v2.2：研究问题、候选机制、方法菜单 |
| [AGENT_HANDOFF.md](AGENT_HANDOFF.md) | 本地实验 Agent 的授权与工程备忘 |
| [DISCUSSION_GUIDELINES.md](DISCUSSION_GUIDELINES.md) | 讨论与研究原则 |

## 目录结构

```
persona-consistency/
├── README.md               本文件
├── EXPERIMENTS_LOG.md      实验记录
├── docs/                   阶段复盘
├── exp/                    全部实验代码（数据构造、闭环压力测试、裁判、训练、表征分析、外部基准）
│   └── results/            各实验的汇总表（纯文本）
├── data/                   精选的小型数据（见 data/README.md）
└── scripts/                编排脚本（vLLM 服务、各轮训练与评测流水线）
```

主要代码入口：

| 环节 | 代码 |
| --- | --- |
| 闭环压力测试与判分 | [exp/e0c_stress.py](exp/e0c_stress.py)、[exp/e0c_judge.py](exp/e0c_judge.py)、[exp/compare_rounds.py](exp/compare_rounds.py) |
| 固定历史机制实验 | [exp/e0d_mechanism.py](exp/e0d_mechanism.py)、[exp/analyze_e0d.py](exp/analyze_e0d.py) |
| 训练数据与 DPO | [exp/e1v5_data.py](exp/e1v5_data.py)、[exp/e1r4_ooc_data.py](exp/e1r4_ooc_data.py)、[exp/e1v5_pairs.py](exp/e1v5_pairs.py)、[exp/verify_ooc_pairs.py](exp/verify_ooc_pairs.py)、[exp/e1_train.py](exp/e1_train.py)（TRL）、[exp/e1_train_lite.py](exp/e1_train_lite.py)（纯 PyTorch，用于 Qwen3.5） |
| 表征分析 | [exp/e0g2_feats.py](exp/e0g2_feats.py)、[exp/e0h_anchor.py](exp/e0h_anchor.py)、[exp/e0k_transfer_steer.py](exp/e0k_transfer_steer.py)、[exp/e0l_assistant_axis.py](exp/e0l_assistant_axis.py) |
| 外部基准 | [exp/run_coser_gca.py](exp/run_coser_gca.py)（按官方 CoSER GCA 逻辑重写，提示词见 [exp/coser_prompts.py](exp/coser_prompts.py)）、[exp/score_apc.py](exp/score_apc.py) |
| 效度审计 | [exp/strict_audit.py](exp/strict_audit.py)、[exp/claim_judge.py](exp/claim_judge.py)、[exp/e0m_grounding.py](exp/e0m_grounding.py)、[exp/e0m_judge.py](exp/e0m_judge.py) |

## 不在 Git 里的内容

模型权重、LoRA 适配器、合并后的检查点、原始生成结果、Hugging Face 缓存，以及 HER / APC / CoSER 的原始文本，都不提交。它们存放在集群上的 `~/rp_persona/`（NFS）和各节点的 `/tmp/xiang_rp/`。`data/` 里的 ID 和脚本足以从公开数据集重建全部输入。

## 与其他子项目的关系

[reason-sensitive-roleplay](../reason-sensitive-roleplay/README.md) 研究“该坚持时不盲从，该改变时不固执”的角色条件决策。本子项目在实验中独立发现的选择性问题（抵抗训练会连带压掉“出戏时如实说明”这类正当让步，见实验记录 P1 / r2″）与它高度相关，两者可以共享评测思路。
