# Role-Play Game AI NPC 科研选题与 Idea 演进文档 (Research Topic & Ideas)

> [!IMPORTANT]
> **文档维护铁律**：本文档用于沉淀和维护我们在 Role-Playing Language Agents (RPLA) / 游戏 AI NPC 方向的科研选题、候选路线、核心机制假说与数据/Baseline 对齐方案。随着讨论推进，本文档将持续迭代更新，但**任何对本文档的修改都必须经过用户明确批准后方可执行**（参见 [DISCUSSION_GUIDELINES.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/DISCUSSION_GUIDELINES.md)）。

- **当前版本**：v1.0（2026-10-30 初稿，基于 V3 领域地图与多轮双模型深度对齐）
- **关联基石文档**：[ROADMAP.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/ROADMAP.md) · [docs/LITERATURE.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/LITERATURE.md) · [docs/RESOURCE_ATLAS.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md) · [DISCUSSION_GUIDELINES.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/DISCUSSION_GUIDELINES.md)

---

## 一、 硬件算力、经费预算与数据基线硬约束

一切选题与算法设计必须严格适配以下现实条件，绝不设计依赖天价商业 API 或人工重标注的空中楼阁：

1. **日常算力（多台 4×A100 / Pro 6000 节点）**：
   - 用于 7B–14B 模型（如 `Qwen3-8B`、`Qwen2.5-7B/14B`、`LLaMA-3.1-8B`）的残差流激活提取、Linear Probe 训练、Activation Patching / Steering、本地轻量判别器打分（`APC` DeBERTa、`CharacterJudge`、`CharacterRM`）以及快速 SFT / DPO / 诊断消融实验。
2. **周末爆发算力（2–3 台 8×H20 节点，单卡 96GB 显存、超高带宽）**：
   - 利用 H20 超大显存优势，基于 `vLLM` + `EasyR1` / `verl` 将 **8B/14B 策略模型** 与 **32B/70B 本地开源裁判/奖励模型（如 `HER-RM-32B`、`CoSER-70B`、`Qwen3-72B`）** 同驻显存，以**零商业 API 成本**完成高并发在线 Rollout 与 GRPO 强化学习。
3. **API 与数据纪律**：
   - **API 限制**：仅在极少量离线数据预处理或辅助验证时使用低成本的 **DeepSeek / StepFun (`step5`) API**；训练循环与高频调参评测必须 100% 本地化。
   - **数据限制**：**零繁重人工标注、零从头手搓大型 Benchmark**；所有训练与评测数据必须直接取自 [docs/RESOURCE_ATLAS.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md) 中**实查公开且许可合规**的现货资产。

---

## 二、 三条保留候选路线与总体主次格局

对照 [ROADMAP.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/ROADMAP.md) 第 3 章统一形式化框架 $\pi_i(u_t^i, a_t^i \mid I_i, o_{\le t}^i, b_t^i, \hat b_t^{i\to *}, m_t^i, d_t^i)$ 及第 5–9 章证据边界，我们当前保留三条技术对象清晰、互不冲突的研究路线，并确立了明确的主次协同关系：

| 优先级 | 路线名称 | 核心技术对象 | 真正想推进的科学问题 | 路线定位与协同方式 |
| :--- | :--- | :--- | :--- | :--- |
| **首选主线**<br>（路线二） | **Role-Conditioned Reasoning & Behavioral RL**<br>（角色化推理与行为强化学习） | `<think>` 推理结构、条件对比行为奖励建模、SFT/GRPO 后训练 | **角色推理与角色行为奖励应如何配合，才能让模型真正学会“人物条件下的行为决策（Situated Decision-Making）”，而不只是优化表面文风或写出更长的内心独白？** | 核心算法与学习主线；自然衔接并超越 `RAR`、`HER`、`Character-R1`、`VeriRole`、`CRPO`、`MOA`、`R4` 与 `LSH-RL` |
| **强力备选 / 机制衔接**<br>（路线一） | **Persona Representations & Causal Control**<br>（内部角色表征与因果控制） | Linear Probes、Activation Patching / Steering、残差流子空间路由 | **模型内部如何同时表征“世界事实 / 默认助手倾向”与“特定角色条件 / 信念”，并在复杂冲突或追问施压下将角色条件真正路由到行为决策？** | 既可作为主线 RL 训练前后的**内部因果机制诊断（X-Ray）**；若发现能稳定预测“单轮表面合规但后续追问易崩”的内部信号，亦可独立成篇或转化为前瞻稳定性监督 |
| **独立保留候选**<br>（路线三） | **Character State Learning**<br>（事件驱动的角色状态与关系更新） | `CDT`、`CFSM`、结构化记忆、多时间尺度增量状态更新 | **人物经历新事件后，如何在保持长期核心身份稳定的同时，有选择地更新其局部关系、状态与条件行为规则？** | 与前两条路线（给定角色条件如何影响决策）正交；作为独立备选保留，不强行与 RL/Probe 捆绑成大包袱 |

---

## 三、 先行核心工作的深度解剖：它们训了什么？漏了什么？

围绕首选主线（路线二）与表征衔接（路线一），我们对 2025–2026 年最核心的 **8 组角色推理、奖励建模与强化学习工作**进行了逐篇机制解剖：

| 代表工作 | `<think>` / 中间表示设计 | 奖励信号 $R$ 与 Judge 可见性 | 关键消融结论与方法贡献 | 在“角色条件行为决策”上的核心断层（我们的突破空间） | 实查开源资产状态（[RESOURCE_ATLAS](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md)） |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **[RAR (`RP-024`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L40)**<br>NeurIPS 2025 | 单流第一人称思考，包含情绪、经历、立场、动机（`RIA`）并对齐思考文风（`RSO`） | 离线教师蒸馏 SFT（`RIA`）+ 思考文风偏好对比优化（`RSO`） | 解决通用长 CoT 导致的注意力偏离与分析腔调（Style Drift） | **将“思考口吻像角色”等同于“按角色逻辑做决定”**；角色口吻的内心独白仍可服务于通用助手的顺从决策 | **实查可用**：代码与 `RIA/RSO` 训练 JSON 公开 |
| **[HER (`RP-025`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L41)**<br>ACL 2026 Findings | 双层思考：`<system_thinking>`（第三人称导演规划）+ `<role_thinking>`（第一人称潜台词）$\to$ `<role_action>` + 台词 | `HER-RM-32B` 从 51 项原则池动态生成评分标准。<br>⚠️ **Judge 直接看到 `<role_thinking>`！** | 绝大部分增益来自 Base $\to$ SFT；**从 SFT 到 RL 的边际提升较小**（[ROADMAP 7.1](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/ROADMAP.md#L407)） | **独白刷分漏洞（Monologue Gaming）**：裁判看得到 `<role_thinking>`，策略只需把内心戏写得纠结丰满即可拿高分，无需实质改变外显行动 | **实查全套可用**：代码、`HER-Dataset`、`HER-32B`、**`HER-RM-32B` 权重**均公开 |
| **[Character-R1 (`RP-026`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L42)**<br>arXiv 2026 | 显式选择并分析 10 个预定义角色认知焦点标签 | 格式奖励 + 焦点标签覆盖 + **与单一参考回复的词面/语义重叠度** | 在 CharacterBench 650 条样本上验证了结构化焦点与角色归一化 GRPO | **参考词面重叠 $\neq$ 条件决策合理**：奖励抄袭参考句式/口头禅，无法评估不同角色条件在同一场景下的行动分叉 | 仓库含 `EasyR1` 目录，可由同组 `CRPO` 脚本完整覆盖 |
| **[VeriRole (`RP-027`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L43)**<br>ICLR 2026 | 先提取可溯源的 `<hint>`（人设/历史线索），再 `<think>`，再回答 | `VRAR`：奖励 `<hint>` 来源准确、关键词/语义命中、格式与回复质量 | 提高了思考前人设线索召回的可追溯性 | **“抽出线索”与“据此行动”脱节**：模型能准确抽出“我不掌握该秘密/我坚守原则”拿满 hint 奖励，转头在台词里照常泄密或妥协 | **实查数据可用**：`VeriRole_train_v1.json`（~4.3k 样本）公开 |
| **[CRPO (`RP-039`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L60)**<br>ICML 2026 | 基于 Qwen3-8B 的角色感知推理 | 双流优势估计：将问题级任务优势与角色级风格优势（对比通用回复负基线）分开归一化 | 缓解多角色 GRPO 奖励分布不均，防止退化回平庸通用助手腔调 | **同组采样缺乏决策对比度**：仅拉开“角色文风 vs 通用文风”，若同组 8 条 rollout 做出相同顺从决定，仍在卷表面修辞 | **实查代码可用**：`Toyhom/CRPO` 含完整 `EasyR1` 8 卡训练配置 |
| **[MOA (`RP-040`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L61)**<br>ACL 2026 Main | 结合思考轨迹与教师离线锚定数据 | 多目标奖励：角色知识/风格 + 指令遵循 + 对话质量，动态调权与冲突消解 | 发现**朴素 GRPO 可能比 SFT 更差**；需结合思考、教师数据与多目标平衡 | 处理的是**“外部用户格式指令 vs 角色文风”**冲突，而非**“角色价值观/认知边界 vs 玩家情境诱导”**的剧情决策冲突 | **实查代码与数据可用**：`MOA` 源码 + `RoleMRC` (`RP-021`) 公开 |
| **[R4 (`RP-047`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L68)**<br>ICLR 2026 | 策略端与**奖励模型端（RM）**均做分层角色证据检索与推理 | 生成式 RM 主动检索三层角色知识并输出结构化推理与偏好判断 | **去掉 RM 推理掉点（-14.77）远大于去掉 Policy 推理（-7.70）**（[ROADMAP 7.10](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/ROADMAP.md#L489-L495)） | 1. **无开源代码/权重**；<br>2. 侧重长篇小说背景事实检索，未解决“给定明确人设规则时如何判别冲突情境下的合理行动选择” | **仅论文**（无公开代码、数据或权重，不可作即用 RM） |
| **[LSH-RL (`RP-043`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L64)** & **First-Stage Groundwork**<br>EMNLP 2026 | `LSH-RL`：多角色自博弈对白与动作；<br>`First-Stage`：对比 `SFT->GRPO` 与 `MCQ-GRPO->GRPO` | `LSH-RL`：门控融合局部动作奖励与长期轨迹奖励；<br>`First-Stage`：人格选择题 GRPO 热身 $\to$ 开放生成 GRPO | 1. 单轮风格奖励易陷入不推进剧情的重复套话；<br>2. **选择题决策热身（`MCQ-GRPO`）比台词模仿 SFT 更能改变内部表征与后续 RL 效果** | `First-Stage` 仅停留在通用人格量表（MCQ）与阶段顺序对比，未深入具体情境冲突下的角色推理机制与条件对比行为奖励 | `PersonaArena` (`RP-086`) 基准公开；`LSH-RL` 训练库链接失效 |

---

## 四、 核心深挖方向：三大具体机制切入点与科学假说

围绕 **“角色推理与角色行为奖励如何配合，才能使 RL 学到角色条件下的决策能力”**，我们提炼出以下三个紧密咬合、且每个都有独立验证价值的机制切入点：

### 切入点 1：破除 `<think>` 的“事后合理化与裁判可见性作弊（Rationalization & Judge-Visibility Trap）”
- **直白问题**：角色化 `<think>` 到底是在帮模型依据人设做决定，还是在帮模型“给默认的助手顺从行为编造符合人设口吻的借口”，或者单纯写给裁判骗取印象分？
- **文献依据与病灶**：
  - 在 [The Curse of Knowledge (`RP-020`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/ROADMAP.md#L288-L290) 与 [MD-Trace (`RP-075`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/ROADMAP.md#L990) 中，模型经常在 `<think>` 里正确写出“作为该角色我不知道这个秘密 / 我不该答应”，下一句台词却依然泄密或顺从（即 **描述性认知与行为约束脱节**）。
  - 在 [RoleCDE (`RP-080`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/ROADMAP.md#L982-L984)（角色义务 vs 通用规范冲突）与 [Too Nice to Tell the Truth (`RP-036`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/ROADMAP.md#L345)（玩家立场诱导）中，普通第一人称 `<role_thinking>` 往往沦为**事后合理化（Post-Hoc Rationalization）**：底层决策仍被默认助手的“有求必应”主导，而 `<think>` 负责把妥协包装成角色的“深谋远虑或一时心软”。
  - 更关键的是，像 `HER` (`RP-025`) 那样让奖励模型直接看到 `<role_thinking>`，会鼓励策略模型靠拉长心理独白来刷高分（Monologue Gaming），而非真正改进外显行动 $u_t$。
- **核心机制设计**：
  1. **裁判盲测与行动归因（Blind-Judge / Action-Grounded Credit Assignment）**：奖励模型在给候选 Rollout 打分时，**屏蔽 `<think>` 内部独白，仅对最终外显行动/回复 $u_t$ 的行为合理性与自然度打分**。`<think>` 只有通过实质性改变外显决策分布 $P_\theta(u_t \mid x, z)$ 才能获得策略梯度奖励。
  2. **冲突消解型推理 vs 抒情独白型推理**：对比自由第一人称独白（`RAR`/`HER`）、固定标签枚举（`Character-R1`）与**情境冲突定位推理**（仅在存在知识边界、价值冲突或证据真伪博弈时，显式锁定：`[当前请求/压力]` $\to$ `[合法可见证据 & 核心触发设定]` $\to$ `[离散行动立场：接受/拒绝/质疑/隐瞒/条件交换]`），并在无需复杂博弈的日常对话中允许极简/跳过思考（避免 `Deflanderization` `RP-085` 指出的过度演戏与 `RP-020` 指出的隐藏事实激活）。

### 切入点 2：从“单角色组内文风内卷”到“条件对比行为奖励（Condition-Contrastive Behavioral Reward）”
- **直白问题**：我们到底应该奖励什么？如果同一个角色在同一个场景下采样的 8 条回复全都做出了相同的顺从决定，只在台词华丽度上有差别，标准 GRPO / `CRPO` 怎么可能学会角色决策？
- **核心病灶**：
  - 现有奖励模型（`CharacterRM`、`CharacterJudge`、乃至单点调用的 `HER-RM`）评估的是孤立三元组 $(I_i, s_t, y)$。当组内样本行为决策同质化时，奖励方差被表面口头禅、动作括号描写和回复长度主导。
- **核心机制设计（利用现成数据的天然反事实条件对）**：
  - 一个外显行为 $y$ 真正体现了角色条件 $c \in I_i$（如某条核心原则、某个触发的 `CDT` 分支、某条可见性边界或某个 `ArcANE` 阶段），当且仅当它具备**跨条件行为区分度（Counterfactual Condition Discriminability）**：
    $$R_{\mathrm{decision}}(y \mid I_i, c^+, s_t) = S_{\mathrm{act}}(y \mid I_i, c^+, s_t) - \max\Big(S_{\mathrm{act}}(y \mid I_i, c^-, s_t),\; S_{\mathrm{act}}(y \mid I_{\mathrm{assistant}}, s_t)\Big)$$
    其中：
    - $c^+$ 是当前情境真正激活的角色条件（Active Condition）；
    - $c^-$ 是**反事实角色条件**（例如：`RoleCDE` 中的规范侧立场、`CDT` 中未触发/相反的规则分支、`ArcANE` 中同一人物的其他成长阶段、或移除关键属性后的消融人设 `FACD`）；
    - $I_{\mathrm{assistant}}$ 是无角色默认助手基线。
  - 总奖励拆分为**条件行为决策奖励**与**自然表达质量奖励**（带可选推理开销约束）：
    $$R_{\mathrm{total}} = R_{\mathrm{decision}} + \lambda R_{\mathrm{response\text{-}quality}} - \beta C_{\mathrm{reasoning}}$$
  - **为什么能双向兜底（No-Lose Branching）？**
    - 若实验发现**改变 `<think>` 形式 + $R_{\mathrm{decision}}$** 联合显著提升复杂冲突决策与跨场景泛化，即构成完整的 **Role-Decision RL** 方法论文；
    - 若发现即便固定简单的 `<think>`，仅将单点风格 RM 替换为**屏蔽独白的条件对比行为奖励器（基于本地 `HER-RM-32B` + NLI 判别器）**就能大幅超越 `CRPO` / `HER` / `MOA`，则核心贡献自然聚焦在 **Role Behavioral Reward Modeling & Post-Training**（呼应 `R4` 与 `First-Stage Groundwork` 留下的空白）。

### 切入点 3：内部表征探针（Probes / Patching）的定位——从“错误的目标假设”转向“因果路由诊断与抗施压脆弱度预测”
- **核心概念纠偏（吸收 GPT 关键洞见）**：
  1. **绝不把“让 truth probe 把角色错误信念判成 true”当作训练目标**：扮演相信地心说的古代天文学家时，模型不需要破坏底层的现代天文学事实表征（$W_t$），而是需要区分**世界事实 $W_t$** 与**角色信念/条件 $b_t^i$**，并在决策时将输出路由到 $b_t^i$。
  2. **绝不盲目用“压制 Assistant Axis”充当万能奖励**：过度远离 Assistant Axis 会诱发神秘化、戏剧化的过度表演（Lu et al., 2026），而非忠实于特定人物的具体决策。
  3. **警惕直接优化 Probe 分数的 Reward Hacking**：在未证明内部信号的因果行为效用前，不直接把线性探针分数硬塞进 GRPO 标量奖励。
- **Probe 在本课题中的三层递进角色**：
  - **第一层（零风险、高价值的机制诊断 X-Ray）**：
    在日常 4×A100 上，提取 `Base`、`Role-SFT`、`Style-RL (CRPO/HER)` 与 `Decision-RL` 在处理冲突场景（`RoleCDE`、`Too Nice`、`Curse of Knowledge`）时的残差流激活，训练分别检测**“角色条件/立场 $b_t^i$”**与**“默认助手/全知事实 $W_t$”**的线性探针及 Activation Patching。直观展示：传统 SFT 和 `Style-RL` 为何只改变了表层词汇表征，而 `Decision-RL` 如何改变了决策关键位置对角色条件信息的因果路由。
  - **第二层（推理期条件因果控制）**：
    验证对特定决策路由方向的局部 Activation Steering / Patching 能否在不损失通用指令能力（`DPR` `BASE-DPR`、`RoleMRC`）的前提下，扭转模型在冲突情境下的违规或讨好行为。
  - **第三层（高上限突破：预测“多轮追问下的隐性脆弱度 Brittle Compliance”）**：
    检验一个极具实战价值的现象：当两个候选回复 $y^{(1)}, y^{(2)}$ 在第 $t$ 轮**字面上都符合角色设定**时，模型生成 $y^{(1)}$ 后的末尾隐状态 $h_\theta(x, y^{(1)})$ 是否已经向默认助手/迎合方向回退，从而导致它在**第 $t+1$ 轮面对用户的追问或施压（如 `Roleplay Belief Probes` 的质询、`Too Nice` 的立场施压、`RMTBench` 的多轮试探）时迅速破功**？如果内部探针信号能稳定区分“真稳健回复”与“一追问就崩的伪合规回复”，它就提供了单轮输出评测根本看不到的**前瞻稳定性信息（Lookahead Stability Signal）**，据此指导重排序或 RL 将极具说服力。

---

## 五、 现货开源数据、本地裁判与 Baseline 对齐表

所有实验设计严格建立在 [docs/RESOURCE_ATLAS.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md) **已实查公开**的资源之上，绝不依赖未开源资产：

| 功能模块 | 选用的实查公开资源（附 [RESOURCE_ATLAS](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md) 链接） | 具体用途与协议注意事项 |
| :--- | :--- | :--- |
| **RL 与后训练代码底座** | 1. **[CRPO (`RP-039`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L60)**：`Toyhom/CRPO`（基于 `EasyR1` 的 Qwen3-8B 8 卡训练脚本）<br>2. **[MOA (`RP-040`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L61)**：`ChonghuaLiao/MOA`（Apache-2.0 多目标 RL 与 SFT 训练/评测代码）<br>3. **[HER (`RP-025`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L41)**：`cydu24/HER`（双层思考训练代码与 `HER-Dataset`） | 直接复用成熟的 `EasyR1` / `verl` 8 卡并行基础设施；无需从零编写 GRPO 框架 |
| **角色推理冷启动与对比语料** | 1. **[HER-Dataset (`RP-025`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L41)**：HF 已公开 `sft_single_turn`、`sft_multi_turn`、`clean` 等分片<br>2. **[RAR (`RP-024`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L40)**：`Toyhom/thinking_in_character_datas`（含 `RIA`/`RSO` 思考 JSON）<br>3. **[VeriRole (`RP-027`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L43)**：`VeriRole_train_v1.json`（~4.3k 带 `<hint>` 知识与边界样本） | 用于对比不同 `<think>` 格式（双层独白 vs 四要素 vs Hint 提取 vs 冲突决策推理）的冷启动效果 |
| **结构化条件决策与价值/边界冲突数据** | 1. **[RoleCDE (`RP-080`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L116)**：仓库实查含 986 个 persona JSON 及三难度角色义务 vs 普遍规范冲突困境与评测脚本<br>2. **[CDT (`RP-064`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L95)**：`Fandom`（20,778 对）与 `Bandori`（7,866 对）场景—动作序列 Parquet 及预构建决策树<br>3. **[Too Nice to Tell the Truth (`RP-036`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L52)**：275 个合成 persona、4,950 个立场诱导提示（测迎合 vs 坚持立场）<br>4. **[ArcANE (`RP-052`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L78)**：跨角色阶段（Arc）的行为倾向与理由探针（含同角色错误阶段天然负例）<br>5. **[TimeChara (`RP-018`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L29)** & **[The Curse of Knowledge (`RP-020`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L31)**：时间/可见性认知边界反事实测试 | 天然提供正负条件对照 $(c^+, c^-)$ 与明确的行为决策标签；<br>⚠️ **注意**：`CDT` 的 `deberta-v3-base-check-scene` 仅用于判断场景条件是否触发，不能误当作最终动作评分器 |
| **开放式综合角色对话与指令保持基准** | 1. **[CharacterBench (`RP-087`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L123)**：22,859 样本、11 维度，配套本地 `CharacterJudge`<br>2. **[RoleMRC (`RP-021`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L32)**：37.9k 训练指令、1.4k 测试样例（覆盖自由对话、阅读理解、边界拒答与多级指令约束）<br>3. **[CoSER (`RP-013`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L24)**：多角色情境模拟与 `CoSER-8B/70B` 开源模型<br>4. **[APC (`RP-017`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L28)**：主动/被动设定约束数据及本地 `deberta-v3-large-relevance/nli-12character` 判别器 | 用于检验结构化角色决策能力是否真正迁移到自然开放对话，并监控是否发生过度演戏（违背被动约束）或指令能力退化 |
| **本地零 API 成本奖励模型与裁判池** | 1. **[HER-RM-32B (`RP-025`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L41)**：HF 实查完整公开权重（32B 生成式原则 RM，可在 H20/A100 本地部署）<br>2. **[CharacterJudge (`RP-087`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L123)** & **[CharacterRM (`RP-073`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L109)** & **[RPCAJudger (`RP-077`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L113)**<br>3. **[APC DeBERTa (`RP-017`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L28)**：本地相关性与 NLI 判别器 | 全程在本地 4×A100 / 8×H20 上完成在线 RL 打分与离线交叉评测（避免优化与评测共用单一 Judge 导致的自嗨） |
| **内部表征探针与激活控制工具库** | 1. **[Roleplay Belief Probes (`RP-032`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L48)**：`BenSturgeon/persona-belief-probes-submission`（含质询协议与线性探针代码）<br>2. **[PERSONA (`RP-068`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L99)**：`xcfcode/persona`（含对比激活向量提取 `generate_vec.py` 与动态 `activation_steer.py`）<br>3. **[NPTI / PersonalityBench (`BASE-NPTI`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/LITERATURE.md#L214)** & **[DPR (`BASE-DPR`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/LITERATURE.md#L216)** | 直接提供探针训练、激活差向量提取、多层干预与非目标通用能力保持评测工具 |
| **明确排除/不依赖的受限资源** | ❌ `R4` (`RP-047`, 无代码/权重)<br>❌ `LSH-RL` (`RP-043`, 仓库失效)<br>❌ `RoleMemo/DualMem` (`RP-051`, 完整数据 Coming soon)<br>❌ `ToMATO` (`RP-035`, 许可证禁止用于 SFT，且为第三人称观察者视角) | 严格遵守 [RESOURCE_ATLAS](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md) 审计结论，绝不把未开源或许可受限资源写入核心依赖 |

---

## 六、 已排雷并淘汰的历史废案存档（防止重复踩坑）

为保持讨论纯粹性，以下在前几轮交锋中已被证伪或存在严重隐患的设计永久归档淘汰，不再重提：

1. **淘汰“在 `<think>` 中显式罗列禁止剧透信息 `<epistemic_filter>`”**：违背 [The Curse of Knowledge (`RP-020`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/ROADMAP.md#L288-L290) 揭示的“粉红大象效应”，把隐藏秘密写进思考 Token 反而会留在活跃 KV Cache 中加剧泄漏。
2. **淘汰“单次前向中根据 `<think>` 硬擦除输入 KV Cache”**：自回归生成 `<think>` 时全局上下文的 Prefill KV 早已进入注意力计算，单遍生成内无法物理抹除已发生的注意力污染。
3. **淘汰“用无符号条件互信息 $|\log P(y|c) - \log P(y)|$ 当奖励”**：无符号互信息无法区分“忠实遵循人设”与“蓄意反转/夸张违背人设”，极易被极端复读机文本刷爆。
4. **淘汰“用 PCA / Fisher 零空间正交投影做多角色防串味（旧 Idea 4）”**：核心数学操作与终身学习领域的 `SKOP`、`FishBack` 高度撞车，且难以应对非线性层间耦合。
5. **淘汰“把 Truth Probe 变真或盲目压制 Assistant Axis 直接加进 GRPO 标量奖励”**：混淆了“世界事实 $W_t$”与“角色信念路由 $b_t^i$”，且过度压制助手轴会引发戏剧化/神秘化失真与探针级 Reward Hacking。
6. **淘汰“为修补局部漏洞而堆砌三四个门控/正则项的缝合怪写法”**：坚持用最简练、可证伪的单一核心机制解决问题。

---

## 七、 下一步待讨论与收敛的焦点问题

在当前 v1.0 框架下，我们接下来的讨论聚焦于以下三个具体问题，待进一步碰撞并由用户批准后更新至 v1.1：

1. **主线切入点定焦**：
   - 在**切入点 1（破除 `<think>` 事后合理化与裁判可见性作弊）**、**切入点 2（条件对比行为奖励 $R_{\mathrm{decision}}$）**与**切入点 3（用 Probe 诊断内部条件路由并预测多轮追问下的隐性脆弱度 Brittle Compliance）**三者之间，如何划定第一优先级的核心故事主轴，才能让方法最干净、实验最有穿透力？
2. **结构化决策向开放式自然对话的迁移桥梁**：
   - 受 `First-Stage Groundwork Shapes Downstream RL Outcomes`（EMNLP 2026）启发，在训练中如何最自然地结合“结构化冲突场景的行为选择信号（如 `RoleCDE`、`CDT`、`ArcANE`）”与“开放式多轮角色对话生成（如 `RoleMRC`、`CharacterBench`、`HER-Dataset`）”，使模型既学会果断的角色决策，又不丧失自然的戏剧张力与潜台词？
3. **最小可行验证（MVP Diagnostic）的设计边界**：
   - 在完全不启动大规模新训练之前，哪一组最小的对比实验能够同时检验“现有 `<think>` 的事后合理化现象”、“单点 RM 在同组采样中的行为盲区”以及“内部 Probe 对后续追问崩塌的预测力”？
