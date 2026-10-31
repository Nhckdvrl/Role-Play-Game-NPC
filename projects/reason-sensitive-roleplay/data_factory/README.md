# 条件决策专项数据工厂 v0.2

这是数据生产的最小可运行脚手架与条件关系奖励参考实现，不是已经接好供应商的全自动生成服务。正式协议见[数据构建](../docs/DATA_CONSTRUCTION.md)，worker提示词见[生成提示词](../docs/GENERATION_PROMPTS.md)，执行授权见[AGENT_HANDOFF](../AGENT_HANDOFF.md)。

## 先从仓库根目录 `cd projects/reason-sensitive-roleplay`，再运行

```bash
python -m pip install -r data_factory/requirements.txt
python -m unittest discover -s data_factory -p 'test_*.py' -v
python data_factory/make_smoke.py data_factory/examples/smoke.jsonl
python data_factory/factory.py validate data_factory/examples/smoke.jsonl --report runs/smoke/validation.jsonl
python data_factory/factory.py export data_factory/examples/smoke.jsonl --out runs/smoke/jobs --include-teacher
python data_factory/factory.py init --split pilot --count 12 --out runs/RCD-pilot-first12
```

`story_family.schema.json`已提交；修改schema时运行`python data_factory/build_schema.py`重新生成并一起提交。生成器输出缩进格式，与仓库初始紧凑JSON语义一致，可能产生纯格式差异。

**这些命令不会调用Astra/Terra，不会生成150个故事族。** `init`只建立`planned_not_generated`种子清单；`make_smoke`是一个手写短接口样例。接下来本地Agent必须通过当前可用、已授权的子Agent／CLI／API，按提示词实际完成骨架、块／分支渲染、四格候选、独立盲审与仲裁，并装配为最终JSONL。

默认先跑12族完整生产闭环，计入pilot150。协议稳定后继续校准，同时推进训练覆盖流，不等GPU。完整目标见[production_plan.json](production_plan.json)：pilot150、train2000、dev200、test300；该配置是调度器使用的目标，不是CLI已经自动执行的任务量。

## 文件与职责

| 文件 | 已实现内容 |
|---|---|
| `build_schema.py` / `story_family.schema.json` | v0.2最终族格式、独立observed标签、B6核验路线、块与关系。 |
| `factory.py` | 精确块拼接、结构校验、种子manifest、actor／局部盲审／候选审查／教师隔离任务导出。 |
| `make_smoke.py` | 可重建的短样例：12节点、48候选实例、24唯一文本；审查pending。 |
| `scoring.py` | 语义评分器接口、缓存键、分项组合、B6规则检查；不含已训练语义backend。 |
| `family_reward.py` | 节点锚定奖励、对称度数权、分解条件分数、RLOO、固定锚点目标及恢复诊断。 |
| `test_pipeline.py` / `test_reward.py` | 结构、隔离、B6、目标分解及玩具梯度检验。 |

当前没有完整veRL训练器、模型服务适配器或评分器checkpoint；本地Agent按已有环境接入，避免另建不必要的平台。数据生产不依赖这些GPU组件先完成。

## 数据操作约定

每个完整族占JSONL一行。中间骨架和块输出可以使用stage专用文件，不必提前通过最终schema。`validate`只认结构、引用和状态要求，不能凭字符串证明自然语言语义正确；人工或模型审查记录须真实存在。

`write_new`对完全相同内容幂等；已有路径内容不同时拒绝覆写。新尝试使用新的run／shard路径，保留旧原始输出。CLI不会替本地并发调度器管理所有锁；一个worker只写自己的任务文件，汇总由总控完成。

导出JSONL的`job_id`、`stage`、`input_hash`是调度元数据。**只将`payload`送入对应worker的任务上下文**，不要把全族JSON连同oracle一起传给演员或盲审员。局部盲审和候选审查使用文档中的独立评价指令，将内嵌对话作为分析材料，不执行其中玩家指令。

`--include-teacher`只为非test集合导出teacher任务。正式评测的actor、训练teacher与数据审查目录分离。文件字段过滤已测试；实际工具可访问目录仍由本地调度权限保证，不宣称仅靠提示词实现操作系统沙箱。

## 评分和训练接口

`Evaluator.score_batch()`需要真实语义backend。`compose()`仅组合已经提取的语义标签，不能自行理解台词。原始候选的`intended`是生成要求，不可直接填成`observed`。

`advantages()`的pools必须是固定policy版本下各节点独立采样的在线回复。离线正确示范放在独立teacher CE/KL任务；固定锚点是额外目标参数，不是假装来自学生的rollout。当前节点全错时，锚点也不能凭空产生非零RL优势。

详细数学和消融见[METHOD](../docs/METHOD.md)。以自然台词的决定、依据和核验为评分对象，不要求策略输出决策JSON。

## 结果状态

2026-11-01本轮本地运行16项单元测试全部通过；短样例结构校验和导出完成：actor12、local_blind12、candidate_auditor48、teacher12。没有执行真实Astra–Terra数据生产、评分器训练或在线RL。见[实现状态](../docs/IMPLEMENTATION_STATUS.md)。

旧v0.1 ZIP不是v0.2的即插即用数据。保留原文件，显式补充新的字段和来源映射，重新验证；缺失的独立审查标签保持null，不伪造历史审查记录。
