# 条件决策与双向历史惯性（专项研究）

**命名说明：**本项目是原仓库主线 A（RL／角色推理）的具体选题，可使用主线 B（Persona Probes／激活控制），并非新增或取代仓库级“方向 A”。旧 A/B、E0/E1/E2 和 RP 编号均保持原义。

## 研究课题：双向历史惯性下的角色条件决策学习

**本专项已确定，现在开展数据生产与方法原型。** 核心问题：多轮角色对话中，模型能否依据人物目标和当前证据改变决定，同时不被此前的合作／拒绝姿态带偏？

该坚持时不盲从，该改变时不固执，信息不足时知道核实什么，并通过自然角色回复表达。研究仍属于纯文本Persona Consistency / Character Fidelity，主要技术路线为教师脚手架内化、条件关系训练与分支信用分配，以及Persona Probe／激活分析。不是把NPC缩成选择题或扩大为完整游戏引擎。

用户已授权Astra总控＋Terra并行合成受控故事族。**数据生产不等待GPU；小批校准与覆盖扩产并行。** 强提示是可利用的教师信号，普通SFT/DPO是比较起点，不是停止后训练的理由。其他候选另行保留。

**本地实际生产状态见 [DATA_PROGRESS.md](DATA_PROGRESS.md)。** 当前已接通独立 Codex CLI 会话，实际调用 `gpt-6.1-terra` 生成／盲审、`gpt-6-astra` 修订／仲裁，并参考公开训练侧真实对话。原始输出、失败和分歧均保留。用户最新明确：数量单位为 **Train 故事族**，先到 5,000，质量和现有资源支持时再考虑 20,000；后者不是自动完成数，也不改变 Pilot 和测试隔离。

## 立即开始

给本地Agent直接使用：**[LOCAL_AGENT_DATA_START.md](prompts/LOCAL_AGENT_DATA_START.md)**。

最短流程：读研究、数据协议和生成提示词 → 运行接口测试 → 实际生成并审查首批12族（计入pilot150）→ 继续校准，同时生产训练覆盖流。不要停在“脚本已写好”，也不要把planned种子清单算成已生成数据。

## 当前文档入口

| 文件 | 用途 |
|---|---|
| **[RESEARCH_PLAN.md](RESEARCH_PLAN.md)** | 研究v3.0：问题、数据对照、教师内化、关系学习、Probe与实验布局。 |
| **[docs/DATA_CONSTRUCTION.md](docs/DATA_CONSTRUCTION.md)** | 数据v0.2：故事族、六分支、四格候选、块置换、B6、隔离审查、划分与扩产。 |
| **[docs/GENERATION_PROMPTS.md](docs/GENERATION_PROMPTS.md)** | Astra及各Terra角色可直接使用的设计／渲染／盲审／仲裁提示词。 |
| **[AGENT_HANDOFF.md](AGENT_HANDOFF.md)** | 本地Agent执行授权、最短命令、首批交付和GPU并行通道。 |
| [docs/METHOD.md](docs/METHOD.md) | 节点锚定奖励、对称度数边权、分解RLOO、固定锚点及独立教师恢复。 |
| [docs/EVALUATOR.md](docs/EVALUATOR.md) | 自由台词多头评分器：独立标签、训练切片、B6语义提取与实测校准。 |
| [data_factory/README.md](data_factory/README.md) | Schema、任务导出、块拼接、评分接口、奖励代码与16项测试的运行入口。 |
| [docs/SOURCES.md](docs/SOURCES.md) | OSPD、Intent-OPSD、Conversational Inertia、CPC-GRPO、COMA／RLOO／DPO依据。 |
| [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) | 已完成代码／文档、实际测试和仍未执行的模型工作。 |
| [DISCUSSION_GUIDELINES.md](DISCUSSION_GUIDELINES.md) | 当前范围、数据授权、自主权与证据原则；已删除冲突的旧数据限制。 |

## 生产目标，不是已完成数量

| 集合 | 目标故事族数 | 定位 |
|---|---:|---|
| 校准 Pilot | 150 | 实际生成、盲审和成本测量；独立开发用途。 |
| 首批训练快照 | 2,000 / 200 / 300 | Train / Dev / Test；供模型尽早使用、同时测量扩产成本。 |
| **本轮合理目标** | **5,000 / 500 / 800** | 训练60,000节点、240,000条基础四格候选；这是目标，不是已完成数量。 |

**各版本的 Train / Dev / Test 是累计总量，不叠加；Pilot 独立计算。** 5,000训练族已意味着大量生成和独立审查工作，不承诺无条件跑满。先以Pilot估算真实每族调用量、token成本、审查通过率，再在2,000族快照时复核是否值得完成5,000族。**本轮不规划10,000、50,000或100,000族，也不自动扩展上限**；未来有实际数据收益与资源依据，再单独修订。训练、评分器和Probe无需等最终规模完成。测试始终按人物／故事骨架分组隔离。

初始训练70%覆盖流、30%困难流；GPU未回报时先构造design-hard，得到真实失败后增加model-hard。机制子集使用同一批独立已结对话块的程序置换。B6必须指出缺失条件并提出可执行核验；四格候选的生成意图和独立审查标签分开保存。

## 代码与状态

```bash
python -m pip install -r data_factory/requirements.txt
python -m unittest discover -s data_factory -p 'test_*.py' -v
```

本轮本地**30项单元测试通过**；短接口样例的结构验证、隔离任务导出、种子清单创建已跑通。样例为1族、12节点、48候选实例／24唯一文本，审查pending；它不是正式生产集。

真实 Astra–Terra 数据生产与独立审查已经执行，首批交付详见 [DATA_PROGRESS](DATA_PROGRESS.md)；语义评分器训练、Probe 和在线 RL 尚未执行。`factory.py`仍只负责数据接口，实际调用由 `agent_dispatch.py` 接入本地已授权 CLI。`scoring.py`提供接口与规则组合，不含已训练语言理解backend；奖励代码也不是完整veRL trainer。全错节点的教师恢复是独立CE/KL任务，不把离线示范伪装成在线采样。

## 领域地图与历史资产

[ROADMAP.md](../../ROADMAP.md)仍是18章领域地图；[docs/LITERATURE.md](../../docs/LITERATURE.md)保留2026-10-30的113篇去重文献快照；[docs/RESOURCE_ATLAS.md](../../docs/RESOURCE_ATLAS.md)保留107项资源快照。全景覆盖身份、动机、知识／信念、记忆／关系、成长、玩家交互与相关接口，不等于本轮必须全部实现。

原RP-001–RP-113编号和阅读／资源状态不因这次立项更新被改写。新增方法来源单列于本专项补充页，不虚增已核读数量。资源可用性、许可证和版本在实际使用时再冻结。

**更新日期：2026-11-01。** 旧v2.2研究和工程交接保留于提交`08f6891143c6e991c2c8369b66b492c77b257b48`。现有实验、模型与数据不因文档升级被删除；本地Agent保留工作树修改，按当前交接开始真实数据工作。
