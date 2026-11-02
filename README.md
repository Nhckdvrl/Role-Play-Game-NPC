# Role-Play-Game-NPC

研究由大语言模型驱动的角色扮演与游戏 NPC：人物的身份、性格、动机与情绪，知识边界与错误信念，记忆与关系，角色成长，以及面对玩家时自然可信的对白与行为。

本仓库是**总项目**：根目录放领域层面的共享资料，各个具体研究题目放在 `projects/` 下的子项目里，各自独立管理代码、数据与实验记录。

## 子项目

| 子项目 | 研究问题 | 状态（2026-11-02） |
| --- | --- | --- |
| [persona-consistency](projects/persona-consistency/README.md) | 单轮与多轮角色对话中的人设一致性：浅层扮演、多轮人设消退与出戏；聚焦施压下的顺从与在线 DPO 方法 | **已归档（2026-11-02）**。人工审计发现所用裁判把强硬语气误判为纠正，原数值结论作废；经验证裁判重判后现象与训练效果仍在但幅度差异很大。见其 [SUMMARY.md](projects/persona-consistency/SUMMARY.md) |
| [reason-sensitive-roleplay](projects/reason-sensitive-roleplay/README.md) | 多轮角色条件决策与双向历史惯性：该坚持时不盲从、该改变时不固执、信息不足时知道核实什么 | 受控故事族数据生产与方法原型，见其 [DATA_PROGRESS.md](projects/reason-sensitive-roleplay/DATA_PROGRESS.md) |

新的研究题目在 `projects/` 下新建子目录，不改变已有子项目的编号与文档。

## 领域层面的共享资料

| 文件 | 内容 |
| --- | --- |
| [ROADMAP.md](ROADMAP.md) | **18 章领域地图**：研究问题、方法、关键公式、证据与分支联系。它描述领域全景，不是任何子项目必须实现的范围 |
| [docs/LITERATURE.md](docs/LITERATURE.md) | **113 篇去重论文**：7 篇综述、106 篇研究，按主题列出原文、发表状态与阅读深度，全局编号 RP-001–RP-113 |
| [docs/RESOURCE_ATLAS.md](docs/RESOURCE_ATLAS.md) | **107 项资源**：数据、评测、Baseline、代码与模型的发布状态核对；含[评测依赖速查](docs/RESOURCE_ATLAS.md#evaluation-cost) |
| [DUAL_MODEL_WEAKNESSES.md](DUAL_MODEL_WEAKNESSES.md) | **双模型弱点复盘与防偏指南**：Gemini 与 GPT 在前期选题与专项讨论中暴露的典型通病、具体案例与即时纠偏动作，适用于所有子项目的讨论 |

领域地图以 Role-Playing NPC 本身为核心；Game 是有世界状态和玩家干预的交互情境，通用多智能体协作、资源采集、战术与底层部署只作必要背景。地图也覆盖玩家意图与试探、承诺与世界反馈、图像与语音中的人物表现等交叉方向。**领域全景不等于某个子项目的立项范围。**

文献与资源索引的核验快照为 2026-10-30：M 82 篇（主文与必要附录）、T 25 篇（定点核读）、B 6 篇（摘要与资源核查）；92 篇发表于或首发于 2025–2026。资源会变化，使用时冻结版本并检查接口；本地运行不等于零计算成本，也不保证复现原论文分数。

## 目录结构

```
Role-Play-Game-NPC/
├── README.md                      总项目入口（本文件）
├── ROADMAP.md                     领域地图
├── DUAL_MODEL_WEAKNESSES.md       讨论过程复盘与防偏指南
├── docs/                          文献索引、资源地图
└── projects/
    ├── persona-consistency/       子项目（已归档）：长对话人设一致性
    └── reason-sensitive-roleplay/ 子项目：角色条件决策与历史惯性
```

## 仓库约定

- **大文件不进 Git**：模型权重、适配器、检查点、原始生成结果、数据集原文和缓存都留在集群存储上；子项目只提交代码、汇总结果和精选的小型数据，并说明如何重建其余部分。
- **子项目自成一体**：每个子项目有自己的 README、实验记录和数据说明；跨子项目的共享内容放在根目录。
- **结论与证据分开**：实验记录写清楚问题、对照、数据与不确定性；被推翻的结论保留并注明撤回原因。
