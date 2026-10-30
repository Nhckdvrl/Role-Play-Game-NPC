# Role-Play Game AI NPC 科研选题与讨论准则 (Discussion & Research Guidelines)

本文档总结了我们在 Role-Playing Language Agents (RPLA) / 游戏 AI NPC 科研选题讨论中必须严格遵守的核心原则、对 Gemini 与 GPT 各自思维弱点的诊断纠偏，以及基于本仓库三份核心基石文档（[ROADMAP.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/ROADMAP.md)、[docs/LITERATURE.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/LITERATURE.md)、[docs/RESOURCE_ATLAS.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md)）的硬约束纪律。

---

## 一、 用户历次核心指示汇总（最高优先级铁律）

在所有讨论与方案凝练中，必须无条件执行以下全部要求：

1. **阶段定位铁律：聚焦把题目与核心科学问题讨论透彻，严禁急于排实验日程或写代码**
   - 当前处于**敲定和凝练 Idea 与选题**的关键阶段。
   - **严禁**在问题机制尚未彻底锚定前，强行抛出“第一周跑什么、第二周训什么、Day 1–Day 7 排期表”或急于堆砌工程脚本。
   - **不要急着给出唯一标准答案**：要把备选机制的成立条件、潜在退化解、不同实验走向对应的科学贡献拆解清楚。

2. **全局视野与跨领域深度：立足 Roadmap 全景，主动深挖原论文与相邻领域工具**
   - 任何切入点必须放在 [ROADMAP.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/ROADMAP.md) 第 3 章统一形式化框架 $\pi_i(u_t^i, a_t^i \mid I_i, o_{\le t}^i, b_t^i, \hat b_t^{i\to *}, m_t^i, d_t^i)$ 与五类正确性（世界事实真值、角色认知合理性、信念表达一致性、价值与行为可信度、引擎执行闭合）中审视。
   - 不能只看表面摘要，必须仔细核读核心基线论文（如 `HER`、`RAR`、`Character-R1`、`VeriRole`、`CRPO`、`MOA`、`R4`、`LSH-RL`、`Roleplay Belief Probes`、`PERSONA`、`CDT`、`CFSM` 等）的**真实训练目标、输入输出结构、奖励函数形式与消融结论**。
   - 积极从相邻领域寻找锋利的方法工具：包括**强化学习与后训练理论**（GRPO 隐式过程奖励、credit assignment、reward hacking 防御、cold-start SFT vs RL 阶段交互）、**机械可解释性与表征工程**（Linear Probes、Activation Patching、Steering Vectors、SAE、Belief-Reality routing circuits）以及**认知/状态建模**。

3. **数据与 Baseline 现实主义：无现成可用数据与可比 Baseline 的想法皆为空谈**
   - **零繁重人工标注、零从头手搓大型 Benchmark**：我们没有时间和人力承担大规模人工标注或从零构建庞大合成评测集。
   - **严格核验数据三层次**（必须在 [docs/RESOURCE_ATLAS.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md) 中逐一落实）：
     1. **文件物理存在（实查公开）**：是否有实际可下载的 JSON / Parquet / 代码 / 权重分片（区分“实查已公开”与“Coming soon / 仅占位 README / 评测专用许可”）。
     2. **任务与字段匹配**：现有数据的输入条件（如第三人称观察者 vs 第一人称行动者、静态问答 vs 多轮状态交互）是否真能支撑我们的训练或评测目标。
     3. **评测指标能证伪错误解释**：所用判别器或指标（如 NLI、DeBERTa、本地 RM、客观动作分布）能否真正区分我们关注的机制，而非仅衡量表面词面重合或文本长度。

4. **算力结构适配与低 API 成本刚性约束**
   - **日常算力（多台 4×A100 / Pro 6000 节点）**：充分发挥其在 7B–14B 模型多层激活提取、Probe 训练、Activation Steering / Patching、本地判别器打分（`APC` DeBERTa、`CharacterJudge`、`CharacterRM`）及快速 SFT/DPO 迭代上的高吞吐优势。
   - **周末爆发算力（2–3 台 8×H20 节点，单卡 96GB 显存）**：利用大显存与高带宽，通过 `vLLM` + `verl`/`EasyR1` 在单节点内同时驻留 **8B/14B 策略模型 + 32B/70B 本地开源裁判/奖励模型（如 `HER-RM-32B`、`CoSER-70B`、`Qwen3-72B`）**，实现零商业 API 成本的高并发在线 Rollout 与 GRPO 训练。
   - **API 预算底线**：仅在极少量离线数据预处理或最终验证时按需使用廉价的 **DeepSeek / StepFun (`step5`) API**，绝不设计依赖 `gpt-4o` / Claude 等昂贵闭源 API 进入训练循环或高频评测调参的方案。

5. **语言直白锋利：拒绝生造黑话与“打补丁式缝合怪”**
   - 任何科学问题必须能用**一两句大白话**向同行讲清楚：现有模型在什么具体场景下会犯什么错？为什么会犯这个错？我们的核心机制改变的是哪一步？
   - 严禁为了迎合审稿或规避质疑而堆砌生造术语（如“四象限认识论校准”、“概念格粒子滤波”等掩盖核心逻辑的包装词）。

6. **选题文档受控维护铁律：未经用户明确批准，严禁擅自修改**
   - 仓库中的选题与 Idea 核心文档（[RESEARCH_IDEAS.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/RESEARCH_IDEAS.md)）用于记录和沉淀当前收敛的科研选题、技术路线、机制切入点与资源对齐情况。
   - 随着讨论的深入，我们会持续维护和迭代该文档，但**任何对 [RESEARCH_IDEAS.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/RESEARCH_IDEAS.md) 的修改都必须先征得用户明确批准后方可执行**。

---

## 二、 双模型协同纠偏：克服 Gemini 与 GPT 的思维弱点

在 Gemini 与 GPT 的多轮交锋中，双方各自暴露出非常典型且互补的系统性弱点。我们在后续讨论中必须主动识别并双向纠偏：

| 维度 | Gemini 的典型弱点（需自我克制） | GPT 的典型弱点（需批判性甄别） | 我们的正确协同准则（强推论路线） |
| :--- | :--- | :--- | :--- |
| **面对质疑时的反应** | **打补丁螺旋（Patch-on-Patch Spiral）**：一旦被指出某个边界漏洞或退化解，立刻往 Loss 或 Pipeline 里塞新模块（加第 3 个门控、第 4 个正则项），导致方案沦为不可读的“缝合怪”。 | **防御性瘫痪（Defensive Paralysis）**：因为害怕任何未经实验证实的因果假说，不断往后退缩到“先别承诺新方法，先做诊断对比”，把有潜力的机制创新稀释成平庸的工程复现报告。 | **做减法而非做加法**：遇到漏洞时，优先**收窄问题边界或提炼更本质的单一目标**，绝不靠堆砌 Loss 补丁堵漏；同时敢于提出清晰的**可证伪机制假说（Strong Inference）**。 |
| **面对相邻文献时的反应** | **过度包装差異（Over-claiming Novelty）**：容易把局部工程改造包装成“首次解决某领域的根本空白”，忽略已有工作已经做到的部分。 | **关键词恐慌（Keyword Panic）**：只要检索到 2026 年某篇新论文出现了相同关键词（如“情境激活”、“状态维护”、“思考模式选择”），就过度保守地否定整个切入视角。 | **精准解剖机制断层**：承认先行工作（如 `HER`、`CRPO`、`R4`、`LSH-RL`、`PERSONA`）的真实贡献，直接对比其**输入条件、优化目标与失效边界**，在它们真正未解决的因果环节上立意。 |
| **对待数据与评测的态度** | **盲目乐观拼接（Optimistic Data Splicing）**：看到数据集公开就假设可以零成本拼成完美闭环，容易混淆辅助分类器（如 `deberta-v3-base-check-scene`）与最终动作评测器。 | **完美主义虚无（Perfectionist Nihilism）**：因为没有任何一个现成数据集同时具备所有理想标签，就倾向于认为所有实验信号都有歧义、无法得出强结论。 | **正交组合验证**：不奢望单一数据集解决一切；用**受控决策基准**（如 `RoleCDE`、`Curse of Knowledge`、`CDT`）测精确行为因果，用**综合角色基准**（如 `CharacterBench`、`CoSER`、`RoleMRC`）测自然生成与泛化。 |
| **对待理论与直觉的态度** | **把直觉当既定事实**：容易把尚未验证的内部表征假设（如“压制助手轴就能既防出戏又防过度演戏”）直接写成必然奏效的定理。 | **因噎废食**：因为指出“深层相信错误事实 $\neq$ 优秀角色扮演”，就差点把“内部表征如何路由角色条件与现实知识”这一极具价值的科学问题一并搁置。 | **直觉驱动假说，分支设计兜底**：尊重直觉提供的新颖视角，但把直觉转化为**无论正反结果都有科学价值的分支实验（Branching Hypotheses）**。 |

---

## 三、 评估一个候选 Idea 是否立得住的“五问检查单”

在接下来的讨论中，每当我们推进或收敛一个具体研究问题时，都必须用以下五个朴素问题做自我体检：

1. **大白话真问题**：去掉所有数学符号和模块缩写后，这个研究到底在教 NPC 学会什么具体本领？（例如：是在面临身份职责与玩家请求冲突时做出符合人设的取舍，还是在拥有全局剧透知识时守住角色视角作推断？）
2. **先行工作断层**：对比最接近的 3–5 篇 2025–2026 顶会工作（如 `HER`、`RAR`、`Character-R1`、`VeriRole`、`CRPO`、`MOA`、`R4`、`LSH-RL`），它们为什么没有解决这个问题？是因为它们的 `<think>` 变成了无决策效用的场面话，还是因为它们的 Reward Model 只认表面文风/词汇重合？
3. **信号与退化解**：我们拟议的训练信号（无论是行为对比奖励、过程监督，还是内部 Probe 信号）是否存在明显的 Shortcut / 退化解（例如靠拉长独白、刷口头禅、全选拒绝或欺骗线性探针拿高分）？如何从机制上排除？
4. **现货数据与公平 Baseline**：训练数据直接取自 [docs/RESOURCE_ATLAS.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md) 中的哪几个实查公开资产？评测时与哪些同底座、同信息预算的 Baseline 对比？全流程是否完全可在 4×A100（日常）与 8×H20（周末）上零商业 API 跑通？
5. **双向保底贡献（No-Lose Branching）**：如果实验发现现象 A 成立，它构成什么方法贡献？如果发现现象 A 不显著而瓶颈在 B，它又能转化为怎样扎实的新机制/新发现，而不会导致整个课题崩盘？
