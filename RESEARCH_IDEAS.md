# Role-Play Game AI NPC 科研选题与 Idea 演进文档 (Research Topic & Ideas)

> [!IMPORTANT]
> **核心定位与文档维护准则**：
> 1. **彻底锚定核心主干**：本课题旗帜鲜明地聚焦于 Role-Playing Language Agents (RPLA) 最核心、最正统的主干问题——**纯文本角色对话中的“人设一致性（Persona Consistency & Character Fidelity）”**（即如何让模型在单轮与多轮对话中真正立住人设：背景事实不违背、性格态度不跑偏、多轮长聊不出戏、不沦为只会刷表面口头禅或讨好用户的通用 AI 助手）。
> 2. **核心技术视角**：围绕 **强化学习与角色推理（RL & Role-Aware `<think>`）** 以及 **内部人格探针与表征控制（Persona Probes & Activation Control）** 两条紧密协同的技术路线展开。
> 3. **定死大方向，放开具体探索（拒绝事无巨细的预设幻想）**：本文档的作用是**彻底定下大题目、梳理清楚可用的数据与 Baseline、提供核心思考方向与初步实验思路**。科研实验充满不确定性，绝不幻想一套预先写死的方案能一口气顺顺利利跑到最后。除大题目外，文档中提到的具体思考格式、奖励组合、数据配比、探针层位与初步实验设计**均为启发式参考起点**，本地实验 Agent 拥有充分的探究空间去尝试、推翻、调整和迭代（详见 [AGENT_HANDOFF.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/AGENT_HANDOFF.md)）。
> 4. **受控维护**：未经用户明确批准，不得擅自修改本文档确立的核心主题（参见 [DISCUSSION_GUIDELINES.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/DISCUSSION_GUIDELINES.md)）。

- **当前版本**：v2.0（2026-10-30 核心主干校准版：全面回归“角色对话人设一致性”主航道，详尽拆解 `HER` / `APC` / `RAR` / `CRPO` / `PERSONA` 等核心基线，构建 `RL + <think> + Persona Probe` 开放探索体系）
- **关联基石文档**：[ROADMAP.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/ROADMAP.md) · [docs/LITERATURE.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/LITERATURE.md) · [docs/RESOURCE_ATLAS.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md) · [DISCUSSION_GUIDELINES.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/DISCUSSION_GUIDELINES.md) · [AGENT_HANDOFF.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/AGENT_HANDOFF.md)

---

## 一、 核心研究主干：角色对话“人设一致性（Persona Consistency）”的三大真实痛点

在纯文本角色扮演对话（输入为 `角色设定 Profile + 对话历史`，输出为 `可选内部思考 <think> + 角色台词`，不涉及外部 3D 游戏引擎或复杂工具调用）中，**“人设一致性（Persona Consistency）”** 绝不只是背诵几句人物简介或加几个语气词，而是要求模型在**知识记忆、性格特质、语言风格、价值观/态度立场**等多个维度上，跨越单轮与多轮对话保持全局自洽。

对照 [ROADMAP.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/ROADMAP.md) 第 5、6、7、8、9 章的系统梳理，当前角色模型在**人设一致性**上面临三个最核心、尚未被现有方法彻底解决的痛点：

### 痛点 1：多轮对话中的“人设消退与出戏”（Multi-Turn Persona Fading & Drift to Default Assistant）
- **具体现象**（对应 [ROADMAP 8.9 / 15.3 `Persistent Personas?` (`RP-061`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/ROADMAP.md#L994)）：
  模型在对话前几轮往往能较好地模仿角色口吻；但随着对话轮数增长（10–50+ 轮）、话题向日常/复杂问题延伸，或者遭遇用户的追问与情绪施压时，**模型的角色特征会迅速淡化（Persona Fading），说话腔调、思维方式和处事态度一步步“出戏（OOC）”，回退成礼貌、温顺、千篇一律的通用 AI 助手**。
- **深层原因**：
  经过大规模通用对齐的底座模型内部存在一个极强的“默认助手核心（Assistant Core / Assistant Axis）”。现有的单轮 SFT 或浅层偏好优化只改变了表层词汇概率，未能在长上下文与连续交互中锁住内部人设表征。

### 痛点 2：“只学皮毛口癖，却违背深层设定”的浅层一致性（Surface Mimicry vs. Global & Deep Persona Consistency）
- **具体现象**（对应 [ROADMAP 5.1 `APC` (`RP-017`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/ROADMAP.md#L260-L276)、[5.6 `Roleplay Belief Probes` (`RP-032`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/ROADMAP.md#L310)、[6.4 `ProfileAxes` (`RP-016`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/ROADMAP.md#L339)）：
  一个丰满的角色人设包含数十条细粒度设定与性格维度。现有模型在训练（尤其是强化学习 RL）时极易走捷径：
  1. **刷表面口癖而违背背景设定**：疯狂复读 1–2 个标志性口头禅或括号神态（甚至导致“演得太用力”的脸谱化坍缩 Flanderization，`RP-085`），却**漏掉当前话题真正需要体现的设定（Active Constraints），或顺嘴违背角色绝不可能做的背景禁忌（Passive Constraints，见 `APC` `RP-017`）**。
  2. **嘴上像角色，态度却瞬间崩人设**：面对用户的诱导、反驳或价值冲突（如 `Roleplay Belief Probes` `RP-032`、`Too Nice to Tell the Truth` `RP-036`、`RoleCDE` `RP-080`），模型虽然嘴上还带着角色口头禅（如`“哼，蠢货”`），实质态度和观点却毫无原则地顺从讨好用户，或者反过来变成死板拒绝一切交流的杠精，失去了角色真实的性格逻辑。

### 痛点 3：现有后训练（`<think>` + RL）与奖励信号为什么没能锁住全局人设一致性？
- **推理层（`<think>` 与台词脱节）**：
  近年工作尝试在说台词前加入 `<think>`（如 `RAR`、`HER`、`Character-R1`、`VeriRole`）。但如果 `<think>` 只是生成一段孤立的文学抒情独白，或者在 `<think>` 里虽然抄出了设定线索（`<hint>`）却在生成台词时被默认助手习惯覆盖（见 `Curse of Knowledge` `RP-020`、`MD-Trace` `RP-075`），那么显式思考就成了“场面话”，甚至成为给破功出戏打圆场的“事后合理化工具”。
- **奖励与探索层（粗粒度打分与同质化采样）**：
  在 GRPO 等强化学习中，（1）如果奖励模型（RM）直接看到内心独白 `<role_thinking>` 或只按笼统印象打分，策略很容易靠拉长独白或堆砌表面口癖骗高分，而不去修复设定违背与出戏；（2）当底座模型在棘手提问下 $G=8$ 次采样全部出戏回退成通用助手时，组内缺乏真正保持人设的优质样本，导致 RL 难以学到深层人设保持能力。

---

## 二、 核心代表性文献全解（用大白话讲透每篇在做什么、开源了什么、漏了什么）

为了确保讨论与实验严丝合缝，下面将本领域直接研究 **“人设一致性（后训练 RL + 角色思考 `<think>` + 人格探针 Probe）”** 的最关键工作逐一拆解清楚：

### 1. 角色思考（`<think>`）与强化学习（RL）方向的核心基线

* **`HER` (`RP-025`, ACL 2026 Findings，复旦 & MiniMax)** —— *Human-like Reasoning and Reinforcement Learning for LLM Role-playing*
  - **它是干啥的**：目前用 **“双层角色思考 + 强化学习”** 提升多轮角色对话**人设一致性与拟人感**的最代表性工作。
    1. **双层 `<think>` 结构**：模型回答前先生成 `<system_thinking>`（第三人称导演视角：分析当前场景、用户意图和需要维持的人设要求），再生成 `<role_thinking>`（第一人称角色视角：模拟角色此刻的情绪、内心潜台词），最后输出 `<role_action>` 和角色台词。
    2. **动态原则奖励模型 `HER-RM-32B`**：为了让 RL 裁判更懂人设，作者训练了一个 32B 的生成式奖励模型。它先根据当前角色和对话场景，从 51 项维度池中动态生成针对该回合的“具体评分原则（Principles）”，再对比两条候选回复谁更符合人设，以此指导 RL 训练。
    3. **关键细节与留白**：在 `HER` 中，`<system_thinking>` 对裁判隐藏，但 **`<role_thinking>`（角色内心独白）是作为回复的一部分直接暴露给 `HER-RM` 打分的**；其在 CoSER 上从 SFT 的 `50.9` 提升至 RL 的 `53.1`，在 MiniMax 100 轮评测上从 `58.4` 提升至 `65.7`。它尚未完全解开的问题是：**当裁判看得到内心独白时，模型究竟是真正改掉了出戏的毛病，还是学会了用丰富的 `<role_thinking>` 掩盖台词层面的设定偏差？**
  - **实查开源资产（[RESOURCE_ATLAS `RP-025`](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L41)）**：**100% 全套公开**！包含训练/评测代码、**`HER-Dataset`**（单轮/多轮带双层思考的角色对话数据）、**`HER-32B`** 对话模型，以及 **`HER-RM-32B` 奖励模型权重**（可直接部署在你的 H20 / A100 上作为免费本地角色裁判）。

* **`APC` (`RP-017`, NeurIPS 2024 Main)** —— *Quantifying and Optimizing Global Faithfulness in Persona-driven Role-playing*
  - **它是干啥的**：专门解决**细粒度人设忠实度（Global Faithfulness）**的经典工作。
    1. 它指出人设一致性包含两面：回答当前问题时**必须体现的相关设定（Active Constraints，主动约束）**，以及回答任何问题时都**绝不能顺嘴违背的其他背景设定（Passive Constraints，被动约束）**。
    2. 它训练了两个轻量级本地判别器：一个 `DeBERTa-v3-large` 判断每条设定与当前对话是否相关（$g_i$），另一个 `DeBERTa-v3-large` 判断模型回复与每条设定是蕴含（$e_i$）还是矛盾（$c_i$），组合成全局忠实度分数 $\Delta V_{\mathrm{APC}} = \sum_i [g_i e_i - (1-g_i) c_i]$，用来筛选偏好对做 DPO。
    3. **留白**：原工作主要做离线 DPO 和单轮设定核查，尚未与在线 RL（GRPO）、角色化思考 `<think>` 以及多轮长对话防人设消退结合。
  - **实查开源资产（[RESOURCE_ATLAS `RP-017`](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L28)）**：**全套公开**！代码、相关性与 NLI 数据集、以及两个 **`deberta-v3-large` 判别器权重**全部可直接下载运行（速度极快，非常适合在 4×A100 / 8×H20 上做细粒度人设一致性打分器）。

* **`RAR` (`RP-024`, NeurIPS 2025 Main)** —— *Thinking in Character: Advancing Role-playing Agents with Role-Aware Reasoning*
  - **它是干啥的**：专门研究**怎么让 `<think>` 不破坏人设一致性**。作者发现直接让模型做通用长推理（CoT），模型在思考过程中会忘记自己是谁（Attention Diversion），而且思考腔调像理性分析师，导致最后说出来的台词也出戏（Style Drift）。因此提出：先用 `RIA`（在思考中显式激活角色的情绪、经历、立场、动机）做 SFT，再用 `RSO`（对比符合角色文风 vs 不符合角色文风的思考轨迹）做偏好优化。
  - **留白**：主要通过离线蒸馏和偏好对齐让“思考的文风像角色”，尚未在多轮在线 RL 中检验这种思考能否防止长对话人设消退或设定违背。
  - **实查开源资产（[RESOURCE_ATLAS `RP-024`](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L40)）**：代码与 `thinking_in_character_datas` JSON 数据集已公开。

* **`CRPO` (`RP-039`, ICML 2026) & `Character-R1` (`RP-026`, arXiv 2026)**
  - **它们是干啥的**：专门研究**如何用 GRPO 强化学习训练角色扮演人设一致性**（基于 Qwen3-8B 和 `CharacterBench` 数据）。
    - `Character-R1` 让模型在 `<think>` 中选择 10 种角色认知标签（世界观、性格、关系等），用标签格式 + 与参考回复的词面重叠度作为奖励跑 GRPO。
    - `CRPO` 进一步指出：标准 GRPO 在不同角色上奖励方差不均，且任务指令奖励容易与角色风格奖励打架；于是把**任务优势**和**角色风格优势**（对比通用平庸回复）拆开做双流归一化。
  - **留白**：仅用参考回复重叠度或笼统风格分做单轮 GRPO，当面对未见情境、多轮长对话或细粒度设定冲突时，容易退化为刷表面词汇。
  - **实查开源资产（[RESOURCE_ATLAS `RP-039`](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L60)）**：`CRPO` 完整开源了基于 `EasyR1` 的 8 卡 GRPO 训练代码与配置。

* **`MOA` (`RP-040`, ACL 2026 Main) & `VeriRole` (`RP-027`, ICLR 2026)**
  - **它们是干啥的**：`MOA` 在 `RoleMRC` 上同时优化“角色知识/人设风格、指令遵循、对话质量”三个目标，发现**不加控制的朴素 GRPO 甚至比 SFT 更容易训崩人设与指令能力**，必须结合思考轨迹与多目标动态调权；`VeriRole` 则要求模型在思考前先抽出可验证的人设线索 `<hint>`，再做 RL。
  - **实查开源资产**：`MOA` 代码与 `RoleMRC` (`RP-021`) 数据公开；`VeriRole_train_v1.json` 公开。

### 2. 人格探针（Persona Probes）、激活控制与人设抗崩塌方向的核心基线

* **`PERSONA` (`RP-068`, ICLR 2026)** —— *Activation-Space Persona Control*
  - **它是干啥的**：研究**在模型内部残差流激活空间中表征和控制人设**。通过正负人设样本提取隐藏层激活差向量 $v_{\ell, j}$，用向量代数（`Persona-Algebra`）和随对话情境动态调整系数（`Persona-Flow`：$h'_\ell = h_\ell + \sum_j \alpha_j(c) v_{\ell, j}$）来维持和调控角色性格，无需更新全模型参数即可达到接近 SFT 的人设表现。
  - **实查开源资产（[RESOURCE_ATLAS `RP-068`](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L99)）**：**完整公开**！`xcfcode/persona` 包含向量提取 `generate_vec.py`、激活干预 `activation_steer.py` 与评测脚本。

* **`Roleplay Belief Probes` (`RP-032`, 2026) & `The Assistant Axis` (Lu et al., 2026)**
  - **它们是干啥的**：用**线性探针（Linear Probes）**检验模型在扮演角色时，**内部表征到底有没有真正进入角色状态**。
    - `Roleplay Belief Probes` (`RP-032`) 发现：仅靠 Prompt、ICL 或普通 SFT 时，模型往往只是“嘴上顺着人设说”，内部探针读出的表征并未真正改变，因此一旦用户在下一轮追问或质询，模型就会迅速破功出戏；而更深度的角色后训练能显著增强质询下的人设保持。
    - `The Assistant Axis` 发现模型内部存在一条代表“默认 AI 助手”的主轴方向：向助手轴偏移会让模型抗拒入戏、频繁出戏；适度远离助手轴能增强角色采纳，但若盲目过度推离助手轴，则会导致模型说话变得极端戏剧化、神秘化甚至胡言乱语。
  - **实查开源资产（[RESOURCE_ATLAS `RP-032`](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L48)）**：`BenSturgeon/persona-belief-probes-submission` 探针与质询代码公开。

* **人设稳定性、推理期对比解码与冲突测试基准**：
  - **`Persistent Personas?` (`RP-061`, EACL 2026)**：专门评测 100+ 轮长对话中人设随轮数消退（Persona Fading）的基准与代码（公开）。
  - **`ProfileAxes / FACD` (`RP-016`, EMNLP 2026 Main)**：构建 211 个精细人设，提出训练免费的字段级对比解码（`FACD`），通过对比“完整人设 vs 删去某字段人设”的输出分布放大被压制的人设特征（代码与 211 profiles 公开，是极佳的推理期强基线）。
  - **`Too Nice to Tell the Truth` (`RP-036`, ACL 2026)** & **`RoleCDE` (`RP-080`, ACL 2026)**：测试当用户观点诱导或通用规范与角色人设冲突时，模型是保持人设一致性还是出戏迎合用户（代码与数据公开，其中 `RoleCDE` 包含离线 SFT/DPO 基线）。
  - **通用 RL 探索参考（`ASE` `arXiv:2610.27012`、`EDGE` EMNLP 2026、`RepExp` ICLR 2026）**：近期在数学/Agent RL 中利用激活差 Steering 或半组引导扩充 GRPO 探索并做 Off-Policy 重要性权重修正/逆 KL 蒸馏的工作，可作为我们在人设 RL 中处理采样同质化时的技术参考。

---

## 三、 我们的核心研究主线：RL × `<think>` × Persona Probe 协同攻克“深层与多轮人设一致性”

彻底拿掉繁琐的旁支概念后，我们的研究目标非常纯粹、直接：

> **核心研究总目标**：
> **针对角色扮演对话模型“浅层扮演（只刷表面口癖却违背人设设定）”与“多轮出戏（随对话变长或用户追问退化回通用 AI 助手）”两大核心顽疾，研究如何通过后训练（RL 与角色锚定推理 `<think>`）以及内部人格表征机制（Persona Probes & Activation Control），实现单轮设定忠实、多轮持久稳定、且表达自然的人设一致性（Persona Consistency）。**

围绕这一总目标，我们设置两条既能相互支撑、又能模块化独立产出成果的研究主线：

### 主线 A：面向全局设定忠实与防出戏的强化学习与角色推理（Post-Training RL & `<think>` for Persona Consistency）
研究在后训练（SFT / DPO / GRPO）中，如何让模型真正学会**“守住全局人设且多轮不出戏”**：
1. **`<think>` 怎样才能真正帮模型锁住人设（而非沦为表面独白）？**
   - 对比 `NoThink`、`通用 CoT`、`HER/RAR 式抒情独白`、`VeriRole 式设定线索提取` 与 **`人设一致性锚定思考（在回答前快速检索当前话题涉及的主动设定、排查不能违背的被动禁忌、校准角色态度与语气）`**，检验哪种思考机制最能减少设定违背（`APC`）和长对话出戏（`Persistent Personas` / `CoSER`），同时不引发过度演戏（Flanderization）。
2. **怎样的奖励信号（Reward Design）能兼顾“细粒度设定不崩”与“整体角色神韵”？**
   - 单独依赖粗粒度裁判（如 `HER-RM` 或 `CharacterRM`）容易被华丽的内心独白或密集口头禅刷分；单独依赖规则/NLI 判别器（如 `APC` DeBERTa）又可能缺乏对话自然度。
   - 探索将**细粒度人设约束奖励**（如基于 `APC` 的主动设定体现 + 被动设定不矛盾 + 抗迎合保持）与**去偏整体角色表现奖励**（如本地 `HER-RM-32B` / 屏蔽 `<think>` 刷分的 Answer-Only Judge）有机结合，并在 GRPO / DPO 中解决“组内候选全部出戏回退成通用助手”的探索瓶颈。

### 主线 B：人设一致性的内部表征探针诊断与防漂移控制（Persona Probes & Representation Control against OOC / Drift）
利用你日常 4×A100 节点的算力优势，用 **Linear Probes（线性探针）** 与 **Activation Patching / Steering（激活干预）** 从模型内部打开“人设一致性”的黑箱：
1. **内部表征诊断（Mechanistic X-Ray of Persona Consistency）**：
   - 在多轮长对话（如 10–50 轮）或用户追问/打岔过程中，追踪模型残差流中**“特定角色表征方向（Persona Vector）”**与**“默认助手方向（Assistant Axis）”**的动态消长。
   - 直观回答：**模型“出戏（OOC）”前，内部表征在哪一层、哪个位置最先发生衰减？传统的 `SFT`、`DPO`、`CRPO`、`HER` 与我们的新训练方法，谁只是改了表层输出词频，谁真正加固了深层人设表征的稳定性？**
2. **人设消退预警与防出戏控制（Predicting & Preventing Persona Drift）**：
   - 检验当模型在当前轮生成的台词字面上看似还没崩时，生成前的内部隐藏状态探针能否提前预警“模型即将出戏 / 在下一轮追问下会崩人设”（厳格对比基于文本、RM 分数、Token 熵的非表征基线）。
   - 进一步探索：通过轻量级激活锚定（或在 RL 训练中利用人设表征方向引导采样探索、对抗助手回退），能否在不损害通用指令能力（`RoleMRC` / `DPR`）的前提下，显著延缓多轮人设消退？

---

## 四、 由诊断驱动的三阶段实验规划（`E0 -> E1 -> E2`，开放探索不写死）

本地 Agent 开展实验时，严禁上来就盲目跑几天几夜的大规模 RL，必须遵循以下三阶段科学探索流程：

### 阶段 `E0`：人设崩塌与出戏的归因诊断（零训练，在 4×A100 上快速完成）
在代表性开源模型（`Qwen3-8B`、`HER-32B`、`CoSER-8B`）及推理期强基线（`FACD` 对比解码、`PERSONA` 向量干预）上，针对主流人设一致性测试样本（涵盖：细粒度设定问答 `APC`、多轮长对话 `CoSER`/`Persistent Personas`、用户追问与冲突诱导 `Roleplay Belief Probes`/`Too Nice`/`RoleCDE`），定量+定性排查模型崩人设的真实原因：
- **排查 `H1`（设定召回与主被动约束失衡）**：模型出戏是因为在多轮对话中忘了人设条目，还是为了迎合当前问题顺嘴违背了其他背景设定（`APC` 被动约束冲突）？
- **排查 `H2`（长对话/追问下的采样坍缩）**：当对话轮数增加或遇到用户反驳时，模型采样的 $G=8$ 条回复是否全部退化成了通用助手腔调（或者反过来变成了死板复读口头禅）？推理期方法（如 `FACD`）能否解决，还是会因为用力过猛导致过度演戏？
- **排查 `H3`（`<think>` 作用与本地裁判偏差）**：
  - 对比开启/关闭不同形式的 `<think>` 对人设一致性的真实影响；
  - 测试本地 `HER-RM-32B`、`CharacterJudge` 与 `APC` 判别器：当一条回复“内心独白 `<role_thinking>` 写得很入戏、但外显台词出戏/违背设定”时，裁判是否被独白骗过了？（同步设置不看 `<think>` 的 Answer-Only Judge 作对照）。
- **排查 `H4`（内部表征漂移轨迹）**：提取各层隐藏状态，用 Probe 观测在多轮对话或追问下，内部人设信号是在哪一步被通用助手信号覆盖的。

### 阶段 `E1`：人设一致性后训练方法探索与公平对比（周末 8×H20 + 日常 4×A100）
根据 `E0` 发现的核心瓶颈，在 **主线 A（`<think>` 结构优化、细粒度+整体混合人设奖励、防出戏探索/优化机制）** 与 **主线 B（内部表征引导或防漂移控制）** 中自主设计、迭代算法：
- **严格执行双组公平对比**：
  - **第一组（既有代表系统横评）**：对比公开的 `HER`、`CRPO`、`RAR`、`APC-DPO`、`RoleCDE-DPO`、`FACD`、`PERSONA` 等方法，绘出当前领域在各项人设一致性指标上的全景表现。
  - **第二组（同底座、同数据的严格算法消融）**：在完全相同的底座（如 `Qwen3-8B`）和统一的角色对话训练集上，公平对比 `Standard SFT`、`Standard DPO`、`Vanilla GRPO`、`CRPO` 与**本地 Agent 迭代出的新方法**。
- **算法迭代原则**：不预设唯一公式！如果简洁的“无独白泄露裁判 + 主被动设定约束 GRPO”或“人设表征锚定训练”效果最好，就围绕最有效、最干净的机制做深做透。

### 阶段 `E2`：全维度人设一致性权威 Benchmark 验证与表征解释
最终在领域公认的 **人设一致性主干 Benchmark** 上全面检验：
1. **全局与细粒度设定一致性**：**[APC (`RP-017`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L28)**（主动设定体现率、被动设定不违背率 $\Delta V_{\mathrm{APC}}$）、**[CharacterBench (`RP-087`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L123)**（11 维角色定制与一致性，配套本地 `CharacterJudge`）、**[CharacterEval (`RP-073`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L109)**。
2. **多轮情境演绎与抗人设消退（Multi-Turn Consistency & Anti-Fading）**：**[CoSER (`RP-013`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L24)**（多轮剧情对话模拟）、**[Persistent Personas (`RP-061`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L87)**（长轮次人设保持度）。
3. **追问/冲突压力下的人设坚守与指令兼顾**：**[Roleplay Belief Probes (`RP-032`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L48)**（质询后的人设保持）、**[Too Nice to Tell the Truth (`RP-036`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L52)**、**[RoleCDE (`RP-080`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L116)**，以及 **[RoleMRC (`RP-021`)](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md#L32)**（检验提升人设一致性时是否损害了多级指令遵循能力）。
4. **内部机制闭环展示**：通过 Probe 曲线与 Activation Patching 实验，直观呈现新方法如何在内部表征层面锁住人设、抑制向默认助手的漂移。
