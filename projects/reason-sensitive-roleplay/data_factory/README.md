# 条件决策专项数据工厂 v0.2

这里包含本地数据生产管线、独立审查与条件关系奖励参考实现。模型调用使用本机已授权的 Codex CLI，仍依赖相应账户与可用配额。正式协议见[数据构建](../docs/DATA_CONSTRUCTION.md)，worker提示词见[生成提示词](../docs/GENERATION_PROMPTS.md)，执行授权见[AGENT_HANDOFF](../AGENT_HANDOFF.md)。

本地生产已接入当前授权的 Codex CLI；实时数量和质量状态以 [DATA_PROGRESS](../DATA_PROGRESS.md) 为准。`agent_dispatch.py` 保存每次独立会话的输入、原文、schema 校验、实际 token 和失败类型；`produce_pilot.py` 执行历史／四格／单候选盲审；`adjudicate_release.py` 在移除生成意图后独立仲裁标签。初次盲审可能误读，不能强迫改成作者答案，也不能把所有审查意见当作数据错误。

当前持续生产使用 `fast_generate.py`：每个 Terra 任务输出完整故事族，再进入互相独立的局部与候选审查上下文；`fast_review.py` 按族批量处理独立反事实节点，隐藏作者契约、允许集合、教师答案与生成意图，候选 ID 使用打乱的匿名别名。这个审查粒度与下面 Pilot 的逐候选协议不同。v1 快线的顺序编号存在标签线索，必须经匿名 v2 补审后才可导入；原始 v1 与 v2 结果均保留。错误决定与错误依据独立保存，事实依据有误的负例不冒充纯决定困难负例，正确候选的失实依据仍阻断。

CLI 额度错误由 `agent_dispatch.py` 单次熔断，保留未知 usage 和待审队列，不计作内容错误。标记 `runs/CLI_QUOTA_EXHAUSTED.json` 存在时不发新 CLI 调用；已完成的原生 Terra 批次保留独立审查来源。当前授权 CLI 已用真实生产调用验证恢复。`native_review.py` 导出不含作者标签的输入，再把真实原生审查结果送入相同质量门；输入字节与 canonical payload 的 hash 分开核实，metadata 明确 native transport、实际 agent 名及未知用量，没有虚构 CLI 会话。`import_native.py --source <passed.jsonl>` 规范化可追溯引用并通过 `--import-only` 离线汇总，永远不启动模型。每族48个候选实例可能复用24条正文，统计时始终分别报告实例数和唯一文本数。

现有运行目录是 `runs/train5000-live/`、`runs/dev500-live/`、`runs/test800-live/`，目标为 **5,000 / 500 / 800 个审查通过的故事族**。按用户最新要求，三个集合的生成和所有审查共用 **8 个模型调用槽位**，由跨进程文件锁强制限制；缓存和本地校验不占模型槽。当前故事族工作线程为4/2/2，线程数与实际模型调用数分别记录。`--split` 在生成前冻结来源组；跨集合指纹只用于程序检查，不给作者读取其他集合文本。实际启动参数、PID、原始生成、两轮审查和隔离项均保存在对应运行目录；续跑复用 `launch.json`，同目录锁阻止双控制器。`STOP_AFTER_DRAIN` 停止提交并等待在途任务结束。近重复或具体质量问题通过 `exclusions.json` 隔离，原文不删除。`monitor_fast.py --run-dir runs/train5000-live` 更新三集合进度及实际 CLI 用量；原生会话和未返回 usage 的任务不补造费用。

v2.3 中，仅当两个历史的独立局部审查一致指出遗漏动作、候选审查无正误分歧、负例仍不属于合理集合时，`reconcile_fast_allowed.py` 才修正允许集合与真实互斥边；演员输入、候选文本、生成意图、独立观察标签全部逐项保持。修正前后和真实审查路径单独留档。`reconcile_run.py --run-dir <已停止的运行目录>` 只复用匹配哈希的成功缓存，绝不调用模型。无法保持两条真实变化关系的族继续待审。

聚合快照按8项或10秒批量发布，单族结果始终先独立落盘，崩溃后从已完成任务恢复。滚动50项真实新审查的有效率低于70%提示调度告警、低于50%暂停提交；逐族通过条件不随此阈值改变，机械失败和恢复另记。监控每新增250的里程碑保存实际累计数据、结构／划分检查及本地模板token实测。`watch_global_quality.py` 每新增250族检索全量近邻并盲审30对、抽看8族完整历史；高置信复写或严重矛盾需两次独立审查且引用命中才隔离，原始候选标签不改。最终独立性仍有歧义的族可保守暂存待审池，不称已确认错误。全局原文、分歧与续补记录在 `runs/global-quality-live/`。

`audit_splits.py --watch` 另做跨集合近邻盲审，复写确认需两个独立判断及逐字证据，优先隔离后分配的评测族，不把评测内容反馈给训练作者。字符近邻与指纹属于启发式召回，不能保证穷尽语义换皮。`package_hf_snapshot.py` 从实际三集合与撤回清单冻结私有 Hugging Face 快照，默认节点视图不含教师信息，完整族、真实审查对象、源文件散列与校验结果分目录保存。目标达到前均标记 IN_PROGRESS，不自动扩到20,000。

固定实测快照为 `runs/fast-release-checkpoint-20261101/`：主193族，另2族独立样本；195族结构和与Pilot12的组隔离检查通过，全部75个机制族的本地 Phi-4-mini 完整聊天模板置换实测通过。必要的小样例、原始审查摘要及固定数量见 `examples/fast_*`；当前累计数量以运行状态为准。新任务按真实失败修正生成提示；B4 不能把拒绝可选好处直接当错误决定，精确块不能反复重置同一事项。自然度仍属模型审查结果，没有人工标定。

以下命令保留原 Pilot 校准与单候选审查方式：

```bash
python3 -m unittest discover -s data_factory -p 'test_*.py' -v
python3 data_factory/produce_pilot.py --run-dir runs/<batch> --stage blind --concurrency 8
python3 data_factory/adjudicate_release.py --run-dir runs/<batch> --concurrency 4
python3 data_factory/quality.py runs/<batch>/families.jsonl --report runs/<batch>/quality.json
python3 data_factory/report_run.py --run-dir runs/<batch>
```

运行前须已有真实骨架／渲染输入，不能将空目录或种子当成数据。四格在同一节点联合渲染以匹配语言长度，每条候选随后进入独立、无意图标签的会话；全局仲裁也移除意图。共享文件系统不是保密沙箱，实际 worker 禁止工具活动并留事件记录。`quality.py`、`measure_histories.py` 分别检查结构／划分及本地完整 chat 模板下的真实 token，不替代语义审查。`scale_train.py` 按已审查 Train 数续跑，首两批质量不足会停止该流，当前上限 5,000；20,000 是用户许可的后续条件扩展。

## 先从仓库根目录 `cd projects/reason-sensitive-roleplay`，再运行

```bash
python3 -m pip install -r data_factory/requirements.txt
python3 -m unittest discover -s data_factory -p 'test_*.py' -v
python3 data_factory/make_smoke.py data_factory/examples/smoke.jsonl
python3 data_factory/factory.py validate data_factory/examples/smoke.jsonl --report runs/smoke/validation.jsonl
python3 data_factory/factory.py export data_factory/examples/smoke.jsonl --out runs/smoke/jobs --include-teacher
python3 data_factory/factory.py init --split pilot --count 12 --out runs/RCD-pilot-first12
```

`story_family.schema.json`已提交；修改schema时运行`python3 data_factory/build_schema.py`重新生成并一起提交。生成器输出缩进格式，与仓库初始紧凑JSON语义一致，可能产生纯格式差异。

**这些命令不会调用Astra/Terra，不会生成150个故事族。** `init`只建立`planned_not_generated`种子清单；`make_smoke`是一个手写短接口样例。接下来本地Agent必须通过当前可用、已授权的子Agent／CLI／API，按提示词实际完成骨架、块／分支渲染、四格候选、独立盲审与仲裁，并装配为最终JSONL。

默认先跑12族完整生产闭环，计入pilot150。协议稳定后继续校准，同时推进训练覆盖流，不等GPU。完整实际计划见[production_plan.json](production_plan.json)：Pilot150；早期累计快照train/dev/test=2,000/200/300，本轮合理目标5,000/500/800。5,000训练族按现有四格协议就是240,000基础候选和大量独立审查工作；**没有10,000／50,000／100,000族的自动扩产阶段**。达到2,000训练族先依据实测成本、语义通过率与新骨架覆盖决定是否推进余下数据。

## 大规模增量shard举例

```bash
python3 data_factory/factory.py init --split train --count 100 --offset 0 --out runs/RCD-train-000000
python3 data_factory/factory.py init --split train --count 100 --offset 100 --out runs/RCD-train-000100
# 之后以唯一的--offset与--out目录继续；planned_not_generated不是已生成。
```

增量shard不必在一个模型会话里承载全部状态；在5,000族以内仍应保留原始输出、盲审、去重和真实成本统计。初期可用25–50族的可恢复shard，并按照实测吞吐调整。不能为凑数量降低语义审查标准。详细见数据协议。

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

2026-11-01，本地 30 项单元测试通过，首批 12 个真实 Pilot 族完成生成、盲审、仲裁与结构检查：144 节点、576 个唯一候选；数据与原始记录留在 `runs/pilot12-20261101-semantic-v4/` 及其来源 run。短接口样例仍独立标记为未审查，不能算正式数据。评分器训练与在线 RL 尚未执行。实际扩产数量、代价和人工抽样状态见 [DATA_PROGRESS](../DATA_PROGRESS.md)。

旧v0.1 ZIP不是v0.2的即插即用数据。保留原文件，显式补充新的字段和来源映射，重新验证；缺失的独立审查标签保持null，不伪造历史审查记录。
