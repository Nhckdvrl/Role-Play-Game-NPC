# 本地 Agent 交接：本专项 数据工作立即开始

> 2026-11-01。当前优先级是**真实数据生产与审查**，不是继续选题或等GPU。用户已授权本专项、Astra总控＋Terra并行生产和研究文档更新。旧交接中的“现成数据为主、只能少量离线API处理”等限制已被本次数据授权替代；训练／高频评分仍以本地开源模型闭环。

## 1. 最短阅读顺序

先读[RESEARCH_IDEAS](RESEARCH_PLAN.md)、[DATA_CONSTRUCTION](docs/DATA_CONSTRUCTION.md)、[GENERATION_PROMPTS](docs/GENERATION_PROMPTS.md)、[data_factory/README](data_factory/README.md)。开始接评分／训练时再读[METHOD](docs/METHOD.md)与[EVALUATOR](docs/EVALUATOR.md)。领域地图和113篇索引是按需工具，不要求读完才能开工。

方向固定：纯文本多轮角色对话的条件决策，避免无理由顺从和无理由拒绝，关注人物目标、证据、自然表达。B/C方向只作储备。不得扩成游戏引擎、复杂状态机、动作空间或单纯二选一benchmark。

## 2. 现在执行的工作

**先检查当前工作树、运行记录和现有数据，保留未提交修改与已有实验。** 更新到本轮文档版本；有远端差异先合并，不reset覆盖其他agent工作。

运行：

```bash
python -m pip install -r data_factory/requirements.txt
python data_factory/build_schema.py
python -m unittest discover -s data_factory -p 'test_*.py' -v
python data_factory/make_smoke.py data_factory/examples/smoke.jsonl
python data_factory/factory.py validate data_factory/examples/smoke.jsonl --report runs/smoke/validation.jsonl
python data_factory/factory.py export data_factory/examples/smoke.jsonl --out runs/smoke/jobs --include-teacher
python data_factory/factory.py init --split pilot --count 12 --out runs/RCD-pilot-first12
```

这些命令只验证接口、建立任务和导出输入，不会自动调用模型。`planned_not_generated`与手写smoke绝不是生产数据。接下来必须实际执行GENERATION_PROMPTS里的设计、渲染与独立审查。

检查当前已有的子Agent／CLI／API和环境变量名，不打印或提交密钥。Astra/Terra为角色名称，映射实际可用工具，不猜API model ID，不把订阅配额当API余额。优先使用已有授权并行能力；新增收费、账户权限或不在授权内的资源才需另行确认。

## 3. 第一批闭环，不再只交计划

总控先领取12个不同故事族，覆盖多类动机、有效／无效理由和至少若干精确块置换族。它们计入pilot150。对子worker分工：骨架设计、独立块渲染、分支与四格渲染、局部盲审、候选盲审、全局审查。每人只接本阶段payload与自己的输出路径，不共享答案上下文。

先完成真实的12族闭环，用实际失败修schema和模板。普通格式错误、批量大小、提示措辞和局部实现由你直接处理，不逐项请用户批准。系统性标签问题才暂停受影响的那类生产，不把全部数据厂停下来重讨论题目。

协议稳定后继续pilot到150，同时准备／生产train覆盖流。**原2,000/200/300只是首个累计快照**，随后推进train/dev/test=20,000/1,000/2,000，再争取50,000/2,000/5,000；新增结构仍有价值且资源允许时向100,000训练族以上持续扩展，不设数量硬上限。各阶段数字不相加。训练与评分器读取已审查的阶段快照，无需等全量数据完成才启动。起始70%覆盖、30%困难；GPU未回报的难例明确标design-hard，不因等待GPU停止覆盖生产。

**规模化任务调度：**从第一批12族后按可恢复shard和`--offset`生产；维持人物动机、世界与证据结构、真假理由、历史长度、preserve/change边等覆盖账本。遇到同构改名、事实不一致或盲审质量下降，单独修有问题的shard／模板，其他生成继续。持续统计真实审查通过的独立族、有效骨架簇、重复率与生成成本；不得用planned种子数抵生产量。

## 4. 最重要的生产约束

- 机制子集先渲染唯一源块，再Python精确置换；不让模型分别重写两段历史。保存块hash、消息顺序和tokenizer／模板测量。
- B6必须点名缺失条件并给可执行核验，不提前承诺。模糊“再考虑一下”不是合格示范。
- 风格匹配但决定错误是核心困难负例；正确且平实的回复可以同样好，不默认负例。
- `intended`不是审查标签；`observed`由独立盲审／仲裁产生。决定、证据、自然度和核验各自标注。
- 按split_group保留人物／模板及其所有改写同集合；test不得用于训练、锚点、评分器、Probe拟合或对抗扩产。
- 只保存真实模型调用和审查记录。解析失败、超时和语义失败分开，不能拿不完整结果冒充accepted。

以上细节的正式定义以DATA_CONSTRUCTION和Schema为准，不在多个地方维护不同版本。

## 5. 评分器与GPU并行通道

数据侧现在就导出候选多维标签，并补充决定正确／依据错误、空泛B6、假核验等切片。GPU侧有资源时先拉起已有可运行的一个基座，测自然输入与同信息脚手架，再逐步接评分器与Probe；不要求四个模型同时就位。

快评分器的真实backend和训练脚本尚需本地实现；仓库目前只有协议、缓存键和分数组合接口。端到端延迟须包含长输入prefill，不承诺毫秒级。

方法原型已经包括共同族目标、对称度数边权、分支RLOO与可选固定锚点目标。全错节点使用独立教师CE/KL恢复；不得把离线正确示范替换进在线采样池后伪造old_log_prob。数据工序不必等待RL trainer就绪。

## 6. 日常记录与交付

沿用已有实验日志；数据可新增一个`DATA_PROGRESS.md`，不要为每批新造一套路线图。每批写明：

```text
run/protocol/schema版本，实际工具／模型与并发配置；
计划／真实生成／结构通过／盲审通过／仲裁通过的族数；
节点、候选实例、唯一候选文本、重复和重试；
覆盖矩阵、B6／困难负例问题、人工抽样状态；
raw/families/reviews/manifest/validation/jobs路径与hash；
本批修改、证据、下一批要完成什么。
```

大数据、原始日志和权重留在约定的本地数据目录；Git提交代码、提示、配置、小样例与路径索引，不提交密钥，不把大产物直接塞进普通Git历史。

本轮第一份交付应是实际故事族与审查报告，而不只是“已经写好脚本／准备开始”。如并行外部接口确实不可用，明确说明缺哪个权限／配置，同时完成当前agent可以生产的真实小批、队列和校验；不伪称已运行Terra集群。

## 7. 自主权与证据边界

你可以自主调整并发、采样、提示、数据比例、局部schema、评分器结构、训练实现和实验先后，记录版本变更即可。方向、数据生产目标、测试隔离与费用边界稳定。无需重新寻求“是否开展本专项”的批准。

鼓励提出方法并用实验改进，不要为防御审稿反复扩充边界讨论。也不得预写三条表征轴或预定成功曲线；数据与模型结果可以推翻解释。代码测试、真实语义审查与GPU训练是不同状态。

## 8. 历史工程资料保留

v2.2完整方案和交接保留于提交`08f6891143c6e991c2c8369b66b492c77b257b48`。原仓库交接第4–5节包含HER/CoSER/RoleMRC/APC格式、CRPO/MOA路径与奖励接口、Probe位置和层号等前期审查线索；按需要从该提交读取，使用时重新核对实际checkout，不把它们当作已完成复现。

当前已有实验、模型和数据一律不因文档升级被删除。新方向的接口实现状态见[IMPLEMENTATION_STATUS](docs/IMPLEMENTATION_STATUS.md)。
