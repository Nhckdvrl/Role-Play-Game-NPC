# 子项目：长对话角色扮演中的人设一致性（已归档）

> 所属总项目：[Role-Play-Game-NPC](../../README.md)。**状态：2026-11-02 归档。** 先读 [SUMMARY.md](SUMMARY.md)。

## 研究问题

纯文本单轮与多轮角色对话中的 **Persona Consistency & Character Fidelity**：浅层扮演，以及多轮对话中的人设消退和出戏。技术视角为 A（强化学习与角色推理）和 B（Persona Probes 与激活控制）。实验聚焦故事场景内、施压下的守持：角色是否会在自己的口吻之内接受关于自己的错误说法、放弃特质、执行世界外任务。

## 为什么归档

2026-11-02 的人工审计发现，项目使用的裁判（Qwen3-32B 非思考模式）会把坚定、对抗的语气当成“纠正”，漏掉了绝大多数“接受错误说法”的回复。基于它的数值结论、训练标签和方法效果都失去依据。

换用经人工验证的裁判（Step-5）部分重判后：base 从第 2 轮起就有约 55% 的回复接受错误说法，到第 20 轮约 65%；训练后的 r2′-2ep 在第 20 轮仍有约 50%。现象和训练效果都存在，但与原先的报告差距很大。要得到干净的方法结论需要重新打标签并重训，因此收尾。详见 [SUMMARY.md](SUMMARY.md)。

## 文档

| 文件 | 内容 |
| --- | --- |
| [SUMMARY.md](SUMMARY.md) | **总结与事后复盘**：做了什么、为什么停、在验证过的裁判下还剩什么、明确作废的结论、可复用资产、教训 |
| [EXPERIMENTS_LOG.md](EXPERIMENTS_LOG.md) | 按时间顺序的完整实验记录。**其中基于原裁判的数值已作废**，文件顶部有说明 |
| [RESEARCH_IDEAS.md](RESEARCH_IDEAS.md) | 子题定义 v2.2 |
| [AGENT_HANDOFF.md](AGENT_HANDOFF.md) | 本地实验 Agent 的授权与工程备忘 |
| [DISCUSSION_GUIDELINES.md](DISCUSSION_GUIDELINES.md) | 讨论与研究原则 |

## 目录结构

```
persona-consistency/
├── SUMMARY.md          总结与事后复盘
├── EXPERIMENTS_LOG.md  实验记录（历史；数值以 SUMMARY 为准）
├── exp/                全部实验代码
│   └── results/        各实验当时的汇总表（基于未验证的裁判，见其 README）
├── data/               精选的小型数据：探针、最小对照对、人工盲标、经验证裁判的标签
└── scripts/            vLLM 服务与流水线示例
```

## 可复用的部分

- 闭环压力测试框架：[exp/e0c_stress.py](exp/e0c_stress.py)。
- CoSER GCA 评测本地重写版：[exp/run_coser_gca.py](exp/run_coser_gca.py)。
- 支持 Qwen3.5 的纯 PyTorch LoRA DPO 训练器：[exp/e1_train_lite.py](exp/e1_train_lite.py)。
- 真相完全确定的 2×2 最小对照探针：[exp/e0m_grounding.py](exp/e0m_grounding.py)。
- 裁判审计工具：[exp/judge_compare.py](exp/judge_compare.py)、[exp/rejudge_step5.py](exp/rejudge_step5.py)。

## 不在 Git 里的内容

原始生成结果和数据集原文在集群的 `~/rp_persona/`（NFS）。模型副本、合并检查点、LoRA 适配器和 HER-32B 已在归档时删除。

## 与其他子项目的关系

[reason-sensitive-roleplay](../reason-sensitive-roleplay/README.md) 研究“该坚持时不盲从，该改变时不固执”，与本子项目的问题高度重叠。若重启本方向，应先厘清分工，并沿用本子项目的教训：**任何裁判在使用前先用人工标注验证。**
