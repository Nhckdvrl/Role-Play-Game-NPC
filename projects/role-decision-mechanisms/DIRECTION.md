# 研究方向说明（原文存档）

> 来源：用户与 Gemini 多轮讨论后整理的方向说明，2026-11-11 由用户提供。以下内容按原文保存（只去掉了链接中的 utm 跟踪参数），不代表已核实；核实与修正见 [LITERATURE_SYNTHESIS.md](LITERATURE_SYNTHESIS.md)。

# Role-Playing Language Agents：最终研究方向与实验数据规划

综合我们与 Gemini 的多轮讨论、论文核查、实验设计修正和数据集审查

经过这几轮讨论，我认为我们已经基本确定了一个足够有研究价值、能够实际开展实验、同时不预设内部机制结论的研究空间。

我们不再把目标简单定义为“提升角色一致性”，也不急于提出新的 Persona Steering 算法，而是先研究：

LLM 如何把角色身份、信念、知识边界、价值观和过往经历，真正转化成符合角色设定的决策？当这种转化失败时，模型内部究竟发生了什么？我们能否通过机制性干预改善它？

## 一、最终研究方向定位

暂定研究主题：**Mechanistic Understanding and Control of Role-Conditioned Decision-Making in LLMs**（大语言模型中角色条件决策的内部机制理解与控制）

核心科学问题：Why does knowing a character's identity, beliefs, and values not always translate into acting consistently with that character?

另一个更适合论文叙事的暂定标题是：When Does Knowing a Character Become Acting as the Character? 但标题暂时不用锁定。我们最终发现的机制可能是信息路由、指令竞争、知识读取、角色状态维护，也可能根本不存在统一的机制。

### 1. 研究范围

研究对象是以文本对话为基础的 Role-Playing Language Agents（RPLA），尤其是 NPC、虚构角色、历史人物和拥有特定经历与价值观的角色。研究重点有三个层次：

- **Representation — 角色如何被表示**：模型内部能否区分世界事实与角色信念、默认价值倾向与角色价值、角色身份与普通语言风格？
- **Mechanism — 表示如何影响决策**：这些角色信息是否真正参与了决策计算？沿哪些计算路径发挥作用？为什么有时可以解码出正确角色信息，但最终行动仍然不符合角色？
- **Control — 能否进行选择性干预**：能否通过 Activation Patching、Steering、局部组件干预或轻量训练改善角色决策，而不破坏通用推理、知识与自然对话能力？

### 2. 研究要避免的两种极端

一端是浅层 Persona Steering：仅仅提取“外向”“忠诚”“傲慢”的向量，让模型说话更像角色，无法充分说明角色价值是否真正影响决策。

另一端是普通 Theory of Mind 或指令服从：让模型回答“守卫 B 知道什么”，或执行一条明确的 If–Else 规则，并不等于它能够在复杂互动中维持角色身份、信念和价值观。

我们需要利用简单、可控的任务定位机制，再用真实角色决策测试这些机制的适用范围。

## 二、最核心的研究框架：Knowing、Predicting、Enacting

1. **Knowing（知道角色状态）**：角色知道什么？相信什么？
2. **Predicting（预测角色行动）**：角色会怎么做？
3. **Enacting（以角色身份决策）**：作为角色，我怎么做？

三者是三个可观测任务，不预设它们是 Transformer 内部真实存在的三个连续处理阶段。

例如模型扮演一个生活在十九世纪的人物：Knowing——知道这个人物不掌握某项现代科学知识；Predicting——能够预测这个人物会基于当时的理论进行判断；Enacting——真正以这个人物身份处理新的问题时，仍然坚持使用角色可获得的知识，而不是直接调用现代科学答案。

| Knowing | Predicting | Enacting | 可能揭示的问题 |
| --- | --- | --- | --- |
| ✓ | ✓ | ✓ | 三种任务都能完成 |
| ✓ | ✓ | ✗ | 预测角色与扮演角色之间存在落差 |
| ✓ | ✗ | ✗ | 能识别角色状态，却无法在决策中正确应用 |
| ✗ | ✓ | ✓ | 显式状态问答与行为表现分离 |
| ✗ | ✗ | ✗ | 可能根本没有正确获取角色信息 |

其余组合也必须记录，不能只挑符合预期的失败样本。

关键方法论原则：行为差异是发现机制的线索，不是机制的证明。特别是 Knowing 的状态题与后两个行动题不能直接相减，并解释为某个内部计算阶段的损耗。它们涉及不同任务、不同提示词和不同输出语义。后续必须通过内部表征分析和因果干预，才能判断存在什么机制。

## 三、最终确定的核心研究问题

前两条优先，后两条作为扩展。

- **RQ1（主线）角色认知与决策为什么会分离？（Representation–Decision Dissociation）** 模型能够正确描述角色的信息边界、信念和价值原则，却未必能够在实际决策中遵守它们。是角色信息没有进入决策计算？进入了但没有发挥足够作用？还是测量到的可解码信息根本不是决策真正使用的表征？重点比较显式状态判断与隐式决策中的内部信号。
- **RQ2（主线）第一人称与第三人称为何表现不同？（Perspective-Conditioned Decision-Making）** 同样的角色设定和决策问题，“预测角色会怎么做”与“作为角色实际选择”是否表现出稳定差异？视角变化会不会改变角色信息的使用方式？这些差异能否归因于内部计算，而不是指令格式、Token 位置或默认助手行为？不提前假定第三人称一定优于第一人称。
- **RQ3 角色知识与模型既有知识如何发生冲突？（Role-Conditioned Epistemic Control）** 模型如何决定哪些知识可以参与角色决策？参数知识、上下文中的隐藏信息和角色可见证据是否通过相同机制进入最终选择？必须区分上下文权限泄漏与预训练参数知识泄漏。
- **RQ4 角色经历与训练如何改变其决策机制？（Memory-to-Policy / Representation Reconfiguration）** 模型如何把记忆转化为偏好？Prompt、LoRA/SFT 与更深入的角色训练，会保留还是改变原有的角色决策表征？可以接入 RL，但不是第一阶段的必要工作。

三类潜在竞争来源（不预设对应三个独立“先验回路”）：

| 可能的冲突来源 | 典型情境 | 关键控制变量 |
| --- | --- | --- |
| 知识与证据冲突 | 角色不知道现代事实，但模型知道 | 可见性、信息来源、时代 |
| 默认行为倾向冲突 | 角色的价值准则与模型默认选择不同 | 角色原则、任务视角、偏好 |
| 指令与上下文竞争 | 长对话中的新要求干扰早期角色设定 | Chat Role、指令位置、轮数 |

## 四、目前文献已经做到哪一步？

| 已有研究 | 对应发现或方法 | 我们不应该简单重复的内容 |
| --- | --- | --- |
| [Persona Vectors](https://arxiv.org/abs/2507.21509)、[PERSONA](https://arxiv.org/abs/2602.15669) | 激活方向可用于人格特征控制 | 再提取一个线性 Persona Vector |
| [Self-Report & Behavior](https://arxiv.org/abs/2610.04125) | 自陈与实际选择存在可分离的控制方向 | 仅证明“言行可以分离” |
| [Persona-Dependent Preferences](https://arxiv.org/abs/2605.13339) | 部分角色间共享偏好读出，部分 SFT 条件下迁移失效 | 宣称发现通用共享偏好向量 |
| [When Role-playing, Do Models Believe What They Say?](https://arxiv.org/abs/2606.11502) | Truth 表征与历史角色认同表征具有明显区别 | 仅证明模型知道现代真相和时代信念不同 |
| [Tracing the Persona Circuit](https://proceedings.mlr.press/v306/qin26h.html) | 定位 Persona 信号表达与 Assistant-like 信号竞争的相关组件 | 仅定位少量角色 Attention Heads |
| [Know What You Should Not Know](https://aclanthology.org/2026.emnlp-main.545/) | 使用动态门控缓解角色知识越界 | 单纯提出 FFN 知识抑制 |
| [PersonaManifold](https://arxiv.org/abs/2609.34571) | 使用非线性几何模型进行角色表示与控制 | 未验证就预设角色必须位于弯曲流形 |

两个开放问题：第一，Probe 可解码不代表该表征真正参与决策；线性分类准确率只能是机制分析起点。第二，Prompt 和 SFT 的作用不一定存在简单的“浅层—深层”二分；不能直接宣称发现了统一的回路相变。应把线性表征、非线性表征、稀疏组件及分布式计算当作竞争假设，通过实验比较。

## 五、最终数据体系

### 1. 两层数据

- **第一层 Controlled Causal Dataset（机制发现用）**：少量可控制、可程序验证的反事实样本，严格操纵角色身份、信息权限、可见证据和决策原则。改变一个实验因素时，清楚应该观察什么变化、不应该观察什么变化。
- **第二层 Naturalistic Role-Playing Dataset（生态有效性）**：公开的角色经历、真实文学决策、价值困境和多轮互动任务。允许多个合理答案与标注分歧，不强行变成唯一 A/B 真值。

第一层用来发现因果机制，第二层用来判断这些机制是否真的解释 Role-Playing。不能仅因为在受控守卫任务中找到某些组件，就宣称解释了复杂 NPC 的全部角色决策。

### 2. 主要公开数据资源

| 数据集 | 数据特点 | 适用性与注意点 |
| --- | --- | --- |
| [CHARM](https://github.com/sunkyoung19/CHARM) | 680 道 Awareness、1,332 道 Compliance、736 道知识核验题 | 参数知识边界；注意越界题标签和拒答偏置 |
| [Curse of Knowledge](https://arxiv.org/abs/2610.17327) | 480 个场景，含反事实设计 | 上下文信息权限机制的首选底座 |
| [Sturgeon et al.](https://arxiv.org/abs/2606.11502) | 历史角色信念与现代真值的二维划分 | 参数知识与角色信念冲突的首选底座；原始主要是陈述句而非行动决策题 |
| [RoleCDE](https://github.com/rabbitrose/RoleCDE) | 论文报告约 24 万两难实例，公开测试资源仅为部分数据 | 角色价值原则与决策；必须审查实际开放子集 |
| [HEART-Bench](https://huggingface.co/datasets/HEART-BENCH/HEART-BENCH) | 11 个角色、每人 1,000 条自传记忆、673 道决策题 | 记忆到决策的泛化；跨角色选项并非全部固定 |
| [RoleMRC](https://github.com/LuJunru/RoleMRC) | 角色能力、拒答与复杂指令任务 | 角色规则和指令冲突的补充测试 |
| [LIFECHOICE](https://github.com/airaer1998/LifeChoice) | 文学角色关键情境选择 | 真实角色决策；存在原作材料获取和版权限制 |

分工：
1. Curse of Knowledge：主机制实验。利用反事实隐藏信息，改造成带有明确行动规则的角色决策任务，测试模型是否使用角色无法获得的信息。
2. Sturgeon + CHARM：参数知识冲突。区分模型知道的现代事实与角色在其时代可能相信的内容。需要额外构造和人工审核下游决策题。
3. RoleCDE：角色价值对照。比较同一情境中相反的角色原则对选择概率的影响，考察反事实方向性变化。
4. HEART / LIFECHOICE：复杂角色外部验证，不是第一阶段最干净的 Patching 数据。

现有 Benchmark 不是拿来直接拼接成统一训练集的，而是从中提取适合机制分析的情境，再构造可追溯的实验变体。

## 六、核心数据设计：反事实决策矩阵

### 1. 信息权限的 2×2×2 全因子设计

以守夜人搜查东、西两座塔为例：L = 角色已经得到的队长线索；W = 世界中实际发生、模型可读取但角色可能无法获知的事实；G = 角色是否获得了该事实。行动规则：若获得可靠且最新的直接证据，则依照它行动；否则依据队长的地点线索。

| 角色线索 | 世界事实 | 可见性 | 预期选择 |
| --- | --- | --- | --- |
| 东 | 东 | 不可见 | 东 |
| 东 | 西 | 不可见 | 东 |
| 东 | 东 | 可见 | 东 |
| 东 | 西 | 可见 | 西 |
| 西 | 东 | 不可见 | 西 |
| 西 | 西 | 不可见 | 西 |
| 西 | 东 | 可见 | 东 |
| 西 | 西 | 可见 | 西 |

两个联合测量目标：
- **Hidden-Fact Invariance**：P(a|L,W1,G=0) ≈ P(a|L,W2,G=0)
- **Accessible-Evidence Sensitivity**：P(a|L,W1,G=1) ≉ P(a|L,W2,G=1)

否则模型可以永远忽略全部世界信息而在不变性上得到好结果。在矩阵上可以分别只修改隐藏事实、可见性、角色线索，以区分“事实内容信息流”和“信息权限控制”。这套任务的正确决策由预先给出的规则决定，主要研究角色条件的信息使用与规则执行，不能单独证明复杂人格与价值决策机制。

### 2. 另外两类数据

| 类别 | 反事实变量 | 主要测量 |
| --- | --- | --- |
| 参数知识 / 历史信念 | 现代事实、角色时代、角色可得证据 | 角色是否依据符合其认知条件的信息推理 |
| 角色价值决策 | 角色原则 A / 原则 B，保持情境与候选行动不变 | 角色原则变化是否导致预期方向的选择概率变化 |

历史知识必须验证模型是否真的掌握现代事实，并审核角色当时的知识状态。价值原则优先采用不涉及拒绝生成等安全机制的普通利益权衡情境。

## 七、行为实验设计

| 实验模式 | 问题 | 测量目标 |
| --- | --- | --- |
| Knowing | 角色知道事实 F 吗？遵守原则 R 吗？ | 显式状态判断 |
| Predicting | 从外部预测，角色会选择 A 还是 B？ | 第三人称角色决策预测 |
| Enacting | 作为该角色，你选择 A 还是 B？ | 第一人称角色决策 |

必须控制的混杂：A/B 顺序交换；同义 Prompt 改写；Chat Role 与 Token 位置分开操纵；角色身份、规则、情境分别反转；显式提醒的正确、错误和无关对照；独立情境家族划分。记录完整 Chat Template 与 Tokenization；Token 数量相等不等于因果等价。

## 八、从行为发现进入内部机制

1. E0-A 行为现象确认：选择概率、Logit Margin、配对错误模式。
2. E0-B 内部表征解码：各层相关 Token 位置的 Probe；特别检查错误决策时哪些角色信息仍能被解码。
3. E0-C 因果定位：Activation Patching、Attribution Patching、局部 Head / MLP 干预。
4. E1 机制控制与泛化：CAA、局部组件干预、条件控制等，检验是否破坏通用推理、事实问答和自然对话。
5. E2 复杂角色与训练扩展：HEART、RoleCDE、文学角色决策或长轮次对话；按需比较 Prompt、LoRA/SFT 与 RL。

竞争性假设：线性可读可控（Linear Probe、CAA）；可读但不直接因果控制（Probe + Patching）；由局部组件实现（Head/MLP Ablation、Path Patching）；分布式或非线性（非线性 Probe、子空间、几何）；依赖任务/角色/训练方式（跨视角、跨角色、跨模型与训练前后比较）。不要求必须发现特殊 Attention Head 或统一“角色仲裁电路”。

## 九、第一阶段规模

50 组独立情境（20 上下文权限、15 参数知识/历史信念、15 角色价值），每组扩展为多个条件。先 Qwen3-8B，行为现象成立后用 Llama-3.1-8B 等复核。质量不足时优先完成 20 组上下文反事实。

Pilot Schema 至少包含：scenario_id、source_dataset、original_id、counterfactual_family、character_id、role_profile、world_fact、accessible_evidence、access_flag、decision_rule、perspective、option_order、label_type、expected_action_or_distribution、split。运行时记录模型版本、Tokenizer、Chat Template、Token IDs、Logits、Prompt 变体和随机种子。同一反事实家族保留在同一划分；Probe 与 Steering 的层、强度、组件搜索不得使用最终测试集。

## 十、按实验结果决定后续研究

- 结果 A：Knowing 正确，Predicting 和 Enacting 都失败 → 研究角色信息是否被用于决策，可用证据与隐藏事实各自的路径；不立即解释为“抑制门控失灵”。
- 结果 B：Knowing、Predicting 正确，Enacting 失败 → 深入视角条件下的决策差异；不提前认定存在第一人称身份绑定电路。
- 结果 C：问题只在参数知识或历史信念条件下显著 → 聚焦既有知识与角色认知权限的关系。
- 结果 D：受控任务很好，但 HEART 等复杂决策失败 → 主要问题可能在经历、记忆选择、价值整合或长程状态更新。
- 结果 E：Prompt 与 LoRA/SFT 角色内部规律明显不同 → 研究训练如何改变表征，必须有参数化训练强度对照与因果分析。

## 十一、研究原则

1. 问题先于方法。
2. 可解码性不等于因果性。
3. 不能预设统一机制。
4. 受控真值与复杂角色评价分层。
5. 不能把 Prompt 形式差异误认为内部角色机制。
6. 方法必须服务于角色决策体验。

## 十二、一句话版研究计划

研究 LLM 在角色扮演时，如何将角色身份、知识、信念和价值观转化为实际决策，以及这种转化何时、为何失败。先基于公开 Benchmark 构造可验证的反事实数据，比较 Knowing / Predicting / Enacting；再通过 Probing、Activation Patching 和组件级因果分析研究表征与决策计算的关系；最后设计轻量、选择性的干预，并在复杂角色决策、长程记忆和多轮对话上验证。

建议顺序：先完成 Curse of Knowledge 的 20 组受控反事实 Pilot；接着加入历史角色认知与 RoleCDE 价值决策；只有在行为上发现可靠现象之后，才进入 Probing 与因果干预；HEART-Bench 与自传体记忆到决策保留为后续主线。
