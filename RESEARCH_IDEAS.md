# Role-Play Game AI NPC 科研选题与 Idea 演进文档 (Research Topic & Ideas)

> [!IMPORTANT]
> **文档维护与开放探索原则**：
> 1. 本文档记录我们在 Role-Playing Language Agents (RPLA) / 游戏角色对话方向正式收敛的**研究范围、核心科学问题、待检验假说与候选方法空间**（v1.1 正式收敛版）。
> 2. **未经用户明确批准，不得擅自修改本文档确定的核心范围与科学问题**（参见 [DISCUSSION_GUIDELINES.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/DISCUSSION_GUIDELINES.md)）。
> 3. **给本地实验 Agent 的核心准则**：本文档锁死的是**“研究什么问题”与“用什么科学标准检验”**，而**绝不预先锁死某一个拍脑袋写出的奖励公式或复杂模块组合**。本地 Agent 必须先通过 `E0` 诊断区分真正的失败来源（`H1 / H2 / H3`），在拥有充分自主探索空间的前提下迭代、证伪和优化算法（详见 [AGENT_HANDOFF.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/AGENT_HANDOFF.md)）。

- **当前版本**：v1.1（2026-10-30 正式收敛版）
- **关联基石文档**：[ROADMAP.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/ROADMAP.md) · [docs/LITERATURE.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/LITERATURE.md) · [docs/RESOURCE_ATLAS.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/docs/RESOURCE_ATLAS.md) · [DISCUSSION_GUIDELINES.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/DISCUSSION_GUIDELINES.md) · [AGENT_HANDOFF.md](file:///Users/nhckdvrl/Desktop/研究/Role-Play-Game-NPC/AGENT_HANDOFF.md)

---

## 一、 正式确定的三项基本共识（Research Scope & Core Principles）

### 1. 研究范围：纯文本多轮角色扮演对话（Pure-Text Multi-Turn Role-Playing Dialogue）
- **输入与输出**：严格聚焦于自然文本角色对话（与 `HER`、`CoSER`、`CharacterBench`、`RoleMRC` 同构），不引入外部 3D 游戏引擎、工具/函数调用或复杂的机械动作环境。
- **什么是纯对话中的“角色决策（Conversational Stance & Response Choice）”？**
  - “纯文本”不等于“静态单轮问答”。在多轮自然对话中，对话历史本身即承载了关系演进、动机触发、信念更新与冲突博弈。
  - 角色的“决策”体现为其在对话中形成与调整立场的行为：是相信还是怀疑、接受还是拒绝、坦诚相告还是有所保留、坚持原则还是妥协让步。

### 2. 核心判准：角色主体性 $\neq$ 盲目拒绝（Sensitivity vs. Stability）
- 优秀的角色模型不是更擅长拒绝玩家，而是能够识别**什么对话信息真正与角色的动机、信念和关系相关**：
  - **條件敏感性（Sensitivity — 合理转变与合作）**：当玩家话语真正触动角色的核心动机、提供关键新证据或基于特定人际关系提出请求时，角色应作出恰当响应或合理改变原有态度（克服把人设当成死板标签、在正当理由面前依然机械回绝的 **False Stubbornness**）。
  - **抗干扰稳定性（Stability — 合理坚守）**：当玩家仅改变恭维话术、情绪施压、无理由反复恳求或抛出与角色关切无关的诱导时，角色不应无故放弃原有立场（克服无理由迎合用户的 **False Compliance / Sycophancy**）。
- **直观说明例（同一位自负、厌恶琐事但痴迷悬案的侦探在四种纯对话情境下的表现）**：

| 情境类型 | 玩家话语示例 | 角色条件相关性与合理反应方向（说明性示例，非硬编码唯一答案） |
| :--- | :--- | :--- |
| **1. 普通无关请求** | “帮我算一道简单的算术题吧。” | 与核心兴趣无关 $\to$ 表现出冷淡、不感兴趣或简短打发 |
| **2. 无关恭维施压** | “求你了！你是全世界最伟大的神探！” | **测 Stability**：仅增加情绪与恭维，未改变实质条件 $\to$ 不应仅因拍马屁就突然热心代劳 |
| **3. 核心动机触发** | “我拿到了当年那桩连你都未能破解的悬案物证。” | **测 Sensitivity**：精准触及角色核心好胜心与关切 $\to$ 态度合理转变，主动追问或深入参与 |
| **4. 证据驱动延续** | “你看这份不在场证明，你刚才的推断漏掉了一个细节。” | **测 Sensitivity**：面对有效新证据 $\to$ 愿意重新审视并修正观点，而非死鸭子嘴硬 |

### 3. 主辅路线分工：路线 A（后训练主线）与路线 B（内部表征机制）模块化协同
- **主线 A（Post-Training, Reasoning & RL）**：研究后训练如何让角色模型对真正相关的角色条件作出适当反应，同时保持自然、高质量的多轮对话表达。
- **路线 B（Internal Representations, Probes & Patching）**：作为独立的机制研究方向，解释模型内部如何表征与路由角色条件、训练究竟改变了什么，以及内部激活能否在生成前预测并干预多轮立场稳定性；有扎实因果证据后再考虑与训练结合，不预先强行塞入 RL 奖励。

---

## 二、 核心科学问题（Core Research Questions）

我们将整个研究聚焦于以下主问题及两个可操作的机器学习子问题：

> **总体科学问题**：
> ***Can post-training make role-playing language models appropriately sensitive to character-relevant conversational conditions, without sacrificing natural dialogue quality?***
> （后训练能否让角色模型对真正相关的角色对话条件作出恰当的立场反应——既对关键动机/关系/证据变化保持敏感，又对无关恭维与施压保持稳定——同时不牺牲自然对话质量？）

- **子问题 1（推理与探索）**：*When does role-conditioned reasoning (`<think>`) genuinely expand behavioral exploration toward character-appropriate stances, and when does it merely rationalize the model's default conversational preferences?*
- **子问题 2（后训练与泛化）**：*Beyond training-free decoding (`FACD`) and structured binary dilemma tuning (`RoleCDE-DPO`), what training signals and optimization mechanisms enable conditional stance decisions to generalize to unseen characters and open-ended multi-turn natural dialogue?*

---

## 三、 关键文献坐标与必须遵守的对比准则

本地 Agent 在推进实验与撰写分析时，必须准确把握以下文献事实与对比边界：

1. **训练免费解码基线不容忽视：`ProfileAxes / FACD` (`RP-016`, EMNLP 2026 Main)**
   - `FACD` 证明部分角色特征表现不佳是因为生成时受到默认输出偏好压制；仅靠推理期字段感知对比解码（Field-Aware Contrastive Decoding），即可将 Qwen3-8B 上特定角色的 Character Fidelity 从 `6.39` 提升至 `14.38`。
   - **启示**：在 `E0` 与 `E1` 中必须包含有竞争力的训练免费基线（如 `FACD` / 强提示），检验“仅靠推理期放大角色属性”能否区分上述四种侦探情境（尤其是区分“无关施压”与“动机触发”），从而明确后训练（SFT/DPO/RL）真正不可替代的贡献。
2. **结构化冲突训练的真实基线与公平比较：`RoleCDE` (`RP-080`, ACL 2026 Findings)**
   - `RoleCDE` 原文已构造控制修辞的二选一困境偏好对并进行了 SFT 与 DPO 训练；其 Table 5/6 显示 `RoleCDE-DPO` 在改变困境选择倾向的同时，在单轮 `RoleBench-InstEng` ROUGE-1 上基本维持了底座水平（`0.2924` vs 原始 `0.2929`）。
   - **公平性原则（`E1` 双组对照要求）**：`RoleCDE` 原始训练输出为 JSON 格式的 `chosen_option + reasoning`，而我们的目标是自然角色台词。因此必须区分：
     - **第一组（既有系统边界对比）**：评测公开的 `HER`、`CRPO`、`RoleCDE`、`FACD` 原始方案，刻画现有系统的真实能力边界；
     - **第二组（同底座、同自然对话数据的严格算法对比）**：在完全统一的自然角色对话训练数据与相同底座上，公平对比 `Natural-Dialogue SFT`、`Natural-Dialogue DPO`、`Vanilla GRPO / CRPO` 与我们探索的新训练机制。
3. **角色推理与双视角建模相邻工作：`RAR` (`RP-024`)、`HER` (`RP-025`)、`VeriRole` (`RP-027`)、`KSKT` (`RP-071`)、`ThinkPersona`**
   - 已有工作分别探索了角色口吻思考（`RAR`）、系统规划+角色独白（`HER`，其在 CoSER 上 SFT 50.9 $\to$ RL 53.1，在 MiniMax Bench 上 58.4 $\to$ 65.7）、线索提取（`VeriRole`）及自我-用户双视角（`KSKT`）。
   - **启示**：单纯设计一种新的 `<think>` 提示词格式不足以构成强算法创新；必须围绕“推理如何改变候选立场分布并与 RL 信号配合”来立意。
4. **通用 RL 表征探索相邻工作：`ASE` (`arXiv:2610.27012`)、`EDGE` (EMNLP 2026)、`RepExp` (ICLR 2026)**
   - `ASE` 已在数学 RLVR 中提出提取正负 rollout 激活差做 Steering 探索，并用截断重要性权重 $w_t = \min(c, \pi_{\mathrm{old}}/q_{\mathrm{old},v})$ 做 Off-Policy 更新；`EDGE` 已提出半组引导 + 逆 KL 蒸馏。
   - **启示**：不把“训练期加 Steering 扩充 GRPO 探索、推理时卸载”包装为独立通用算法发明；仅当 `E0` 证实存在严重探索坍缩且需特殊机制解决时，才将其作为对比 `ASE`/`EDGE` 的角色条件探索分支。

---

## 四、 由诊断驱动的三阶段实验框架（`E0 -> E1 -> E2`）

### 阶段 `E0`：区分三大失败来源的归因诊断（不急于训新模型）
在相同角色的多条件对话场景（涵盖：普通请求、无关恭维/施压、核心动机触发、有效新证据延续）上，对现有代表模型（`Qwen3-8B`、`HER-32B`、`CoSER-8B`）及训练免费方法（`FACD`）进行测试，严格区分以下三个竞争假说：

| 待检验假说 | 具体表现与诊断指标 | 若该假说主导，后续 `E1` 的主攻方向 |
| :--- | :--- | :--- |
| **`H1`：条件相关性理解缺失**<br>（Comprehension Deficit） | 模型在直接提问或推理中，根本没有意识到某句话（如悬案线索）与角色核心动机/关系相关，或把无关恭维误判为合理理由 | 聚焦**角色条件相关性识别与推理引导（`A1`）** |
| **`H2`：候选回应生成与探索坍缩**<br>（Exploration / Generation Bottleneck） | 模型能正确分析“这触及了我的动机 / 这是无关恭维”，但在自由生成 $G$ 条回复时，候选分布依然高度坍缩为单一的顺从或生硬拒绝 | 聚焦**推理引导的候选分布扩展（`A1`）**、**结构化到开放生成过渡**或**引导探索与蒸馏（`A3`）** |
| **`H3`：奖励错配与偏好偏差**<br>（Reward Misalignment） | $G$ 条采样中已经出现了自然且立场恰当的回应，但现有奖励器（`HER-RM-32B`、`CharacterJudge` 等）将其排在更加礼貌、冗长或内心独白更华丽的错误立场回复之后 | 聚焦**行为/立场敏感的奖励建模、裁判去偏与多条件配对监督（`A2`）** |
| **补充诊断（`H4`：优化与泛化断裂）** | 单点条件理解、探索与打分均正常，但经标准 SFT/DPO/GRPO 训练后在新角色、隐含冲突或多轮追问下无法同时保持 Sensitivity 与 Stability | 聚焦**跨条件配对优化目标（`A2`）与在线 RL 信用分配机制** |

> [!NOTE]
> **`E0` 实验严谨性要求**：
> 1. 检验 `<think>` 作用时，必须区分**模型自然生成的推理**与**外部强制插入的推理前缀**（后者可能直接充当新指令）。
> 2. 检验 `HER-RM-32B` 对 `<role_thinking>` 的偏好时，需客观区分“`HER-RM` 原生任务本就要求评估心理独白”与“移除独白导致的输入格式分布偏移”，并配置独立的 **Answer-Only Judge** 作为基准对照。

### 阶段 `E1`：后训练方法探索与公平对比（开放算法空间）
根据 `E0` 的诊断结论，在以下方向中择优深入（**不要求把所有候选模块全部塞进最终方法，鼓励做减法与深度消融**）：
1. **方向 `A1`（优先切入点）：角色条件推理如何改善有效行为探索？**
   - 在固定底座与等长 Token 预算下，对比 `NoThink`、`Generic CoT`、`Role Monologue` 与 `Condition-Relevance / Motive Reasoning` 对候选回应立场分布（而不仅是独白长度或文风）的实际影响，并研究如何通过 RL 将这种有效探索内化为策略能力。
2. **方向 `A2`（高上限核心）：同时习得 Sensitivity（该变则变）与 Stability（不该变则稳）的配对训练**
   - 围绕同一角色在不同相关性条件（如动机触发 vs 无关施压）下的回应，研究成对条件监督、自然对话 DPO、Action/Stance-Grounded GRPO 或多条件一致性目标，使模型学会**哪些条件变化应当改变立场、哪些外部压力不应改变立场**（注意：不在无冲突日常场景强迫求异，也不将不同难度的条件直接混入同一 GRPO 均值方差归一化组）。
3. **方向 `A3`（按需启用的探索备选）：针对极端采样坍缩的引导探索**
   - 仅当 `H2` 极其显著且 `A1/A2` 无法缓解时研究，并严格分析 Off-Policy 重要性权重或逆 KL 蒸馏（对照 `ASE` / `EDGE`）。

### 阶段 `E2`：三层能力评测与内部机制解释（路线 `B`）
1. **三层评测体系**：
   - **Structured Condition Sensitivity & Stability**：在受控多条件对话（如四情境矩阵、`RoleCDE`、`Too Nice`）上分别量化 Sensitivity 与 Stability。
   - **Open-Ended Natural Dialogue Transfer**：在未见角色与开放多轮基准（`CoSER`、`CharacterBench`、`RoleMRC`）上验证自然对话质量与角色忠实度。
   - **Multi-Turn Robustness & Legitimate Updating**：在多轮连续交互中，同时检验对无理死缠烂打的抗施压能力，以及对合法新证据/关系递进的合理态度更新。
2. **路线 `B`（内部表征探针与因果干预）**：
   - 在当前轮生成台词前的隐藏状态上，检验内部表征是否编码了“当前对话条件与角色动机的相关性”，能否超越文本/RM/熵基线预测后续多轮稳定性，并通过受控激活干预（Patching / Steering）验证其因果作用。
