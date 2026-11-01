# 实际生产小样例

`pilot_audited.jsonl`是首批12族中RCD-pilot-00000的完整原样导出，包含两段历史、六分支、48候选与关系边。它来自真实模型生成和独立审查，不是`make_smoke.py`的手写接口fixture。

`pilot_audit_bundle.json`包含该族12条局部盲审、48条单候选盲审、每项输入hash及意图不可见的Astra仲裁原文。可从族内actor输入重建盲审payload并核对hash。原始首次标签和最终观察标签分开保存；模型审查不等同人审，人工状态仍为`not_sampled`。

完整12族、原始调用事件与旧版本位于本地`runs/`，路径及hash在`production_snapshot.json`和专项`DATA_PROGRESS.md`。该小样例的audit引用指向本次本地运行，克隆仓库不会自动包含大日志；配套bundle保留必要的可复核结果。`reference_summary.json`记录真实参考语料来源、训练分区统计与阅读范围，未复制其对话。

`scorer_calibration.jsonl`是额外真实生成并独立盲审的一条候选：当前计时器40分钟，回复以60分钟为据作出本身正确的开炉决定。其决定与依据标签分开，未计入完整故事族或基础四格数量。

`fast_audited.jsonl` 是固定193族快照中的一个完整真实 Train 族。`fast_audit_bundle.json` 保留其生成草稿、两轮独立审查原文和真实 CLI 元数据；匿名候选别名可由草稿与 `fast_review.payloads` 重建，逐条核对 observed 的原始结果索引。此协议按族批量审查，与 Pilot 的单候选会话不同，不能用相同名称掩盖粒度变化。`fast_production_snapshot.json` 记录主193族、另2族独立样本、75个机制族的完整 Phi-4-mini 模板实测及24条独立 Astra 抽查的真实结果。它是固定快照，5,000 Train 仍为正在执行的目标。
