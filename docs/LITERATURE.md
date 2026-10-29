# Role-Playing Agents：论文与证据索引

**核验快照：2026-10-30。主索引 113 篇去重论文（7 篇综述、106 篇研究/benchmark/技术报告），其中 2025–2026 年发表或首发 92 篇。** 阅读等级 M 82 篇、T 25 篇、B 6 篇。M=主文阅读、关键附录按需核对，T=定点核读方法或实验，B=摘要/元数据/资源核查，均不表示已独立复现。R4 的具体正式论文消融已定点核读，本版由 B 改标为 T。

所有论文使用 **RP-001 至 RP-113 唯一编号**，与 [资源地图](RESOURCE_ATLAS.md) 一一对应；同一研究的不同预印本、改名与正式版不重复。七篇综述不另设资源条目，106 篇研究在资源地图有对应记录，另有一个官方挑战 ENV-01。可以按 RP ID 在两个文件中直接检索。

## 主题目录

| 类别 | 核心研究问题 | 论文数 |
| --- | --- | ---: |
| [T1: 综述与领域边界](#topic-1) | 领域概念、任务与评价分类 | 7 |
| [T2: 身份、数据、人设约束与知识边界](#topic-2) | 人设从哪里来，角色此时应知道什么 | 15 |
| [T3: 人物内心推理、性格、情绪与价值](#topic-3) | 为何在特定情境如此思考、感受和选择 | 14 |
| [T4: 训练、奖励建模与多轮优化](#topic-4) | 如何监督开放式角色质量及长程行为 | 12 |
| [T5: 记忆、时间、关系与角色弧线](#topic-5) | 事实、主观解释、关系与阶段怎样变化 | 14 |
| [T6: 符号、参数、激活、解码与架构控制](#topic-6) | 干预发生在规则、参数、激活、解码的哪一层 | 9 |
| [T7: 评价、玩家输入、自然度与安全](#topic-7) | 怎样检验角色自然度和玩家交互 | 20 |
| [T8: 戏剧、社会认知与可执行世界（相邻）](#topic-8) | 多方剧情、承诺执行与局部信念的接口 | 15 |
| [T9: 多模态角色感知、语音与表达](#topic-9) | 角色化视觉、声音与视频表现 | 7 |

<a id="topic-1"></a>
## 1. 综述与领域边界

| 统一论文 ID | 完整题名与入口 | 发表状态 | 阅读 | 方法、证据与适用边界 |
| --- | --- | --- | :---: | --- |
| RP-001 | [From Persona to Personalization: A Survey on Role-Playing Language Agents](https://openreview.net/forum?id=xrO70E8UIZ) · [补充原始记录／版本](https://arxiv.org/abs/2404.18231v2) | TMLR 2024；核读 arXiv v2（2024-10-09） | **M** | 按 demographic、established character、individualized persona 整理数据、构建与评价，覆盖面超过游戏 NPC；三类是对象差异，不是三个技术代际，产品附录也不能作为 2026 年现状证据。 |
| RP-002 | [Two Tales of Persona in LLMs: A Survey of Role-Playing and Personalization](https://aclanthology.org/2024.findings-emnlp.969/) · [核读版本](https://arxiv.org/abs/2406.01171v3) | EMNLP 2024 Findings；核读 arXiv v3（2024-10-05） | **M** | 区分赋予模型的人设与适应用户的人设，并整理环境、角色特征和涌现行为；包括专业任务角色与个性化，不能全部归为虚构人物模拟，作者也未建立跨论文统一榜单。 |
| RP-003 | [The Oscars of AI Theater: A Survey on Role-Playing with Language Models](https://arxiv.org/abs/2407.11484v9) | arXiv，首发 2024；核读 v9（2025-01-10），未核实正式 venue | **M** | 以数据、模型与对齐、智能体架构、评测组织领域，并区分对话质量、人格忠实、行为忠实和吸引力；分类与历史脉络有用，其经验性观点不等于经统一实验确立的普遍定律。 |
| RP-004 | [Towards a Design Guideline for RPA Evaluation: A Survey of Large Language Model-Based Role-Playing Agents](https://aclanthology.org/2025.findings-acl.938/) | ACL 2025 Findings | **M** | 从 1,676 条初始检索记录筛到 122 篇全文纳入研究，归纳六类智能体属性、七类任务与七类指标；支持评价设计与任务属性对齐，不是 1,676 篇全部深入分析或游戏 NPC 的完整覆盖。 |
| RP-005 | [Role-Playing Agents Driven by Large Language Models: Current Status, Challenges, and Future Trends](https://arxiv.org/abs/2601.10122v1) | arXiv v1（2026-01-15） | **T** | 从风格、人格、记忆、数据和评价梳理技术发展；仅定点核读相关章节，三代演进是作者叙述框架，不能据此宣布全领域已统一转向认知建模。 |
| RP-006 | [More Than a Role: Memory in LLM-based Role-Playing Agents](https://github.com/aixiaodewugege/More-Than-a-Role-Memory-in-LLM-based-Role-Playing-Agents) · [补充原始记录／版本](https://pila26-workshop.github.io/) | KDD 2026 PILA Workshop Oral；non-archival，非 KDD 主会 | **M** | 以角色侧和交互侧记忆、承载方式及写入—读取—更新生命周期分析身份保持与关系变化；属于概念综述，未做统一量化元分析，部分二手方法归纳需回到原论文校正。 |
| RP-007 | [Role Consistency in Role-Playing Agents: A Survey of Evaluation, Memory, Reasoning, Alignment, and Safety](https://aclanthology.org/2026.findings-emnlp.625/) | EMNLP 2026 Findings | **M** | 将角色一致性组织为 specification、role-state、reasoning、alignment、evaluation 的系统性质；benchmark 覆盖表是解释性标注，不能替代性能比较，多模态与具身覆盖仍有限。 |

<a id="topic-2"></a>
## 2. 身份、数据、人设约束与知识边界

| 统一论文 ID | 完整题名与入口 | 发表状态 | 阅读 | 方法、证据与适用边界 |
| --- | --- | --- | :---: | --- |
| RP-008 | [Character-LLM: A Trainable Agent for Role-Playing](https://aclanthology.org/2023.emnlp-main.814/) | EMNLP 2023 Main | **M** | 从人物生平合成经历、情绪与 protective experiences，分别训练九个角色，给出越界回答控制的早期证据；教师同时参与数据和评审，单角色参数训练不证明多角色扩展或长期记忆。 |
| RP-009 | [RoleLLM: Benchmarking, Eliciting, and Enhancing Role-Playing Abilities of Large Language Models](https://aclanthology.org/2024.findings-acl.878/) | ACL 2024 Findings | **M** | 以 ContextInstruct、RoleGPT 和 RoCIT 构建角色知识与角色化指令监督及 RoleBench，分别评估指令和角色泛化；风格迁移不保证未见角色专属知识，教师评价与知名角色污染仍限制解释。 |
| RP-010 | [Large Language Models are Superpositions of All Characters: Attaining Arbitrary Role-play via Self-Alignment](https://aclanthology.org/2024.acl-long.423/) | ACL 2024 Main；方法 DITTO | **M** | 用模型自身知识生成 role-specific/role-contrastive 数据进行自对齐，研究角色知识与风格对教师规模的不同依赖；“superposition”是比喻，其边界控制不等于追踪角色时空可知性。 |
| RP-011 | [Capturing Minds, Not Just Words: Enhancing Role-Playing Language Models with Personality-Indicative Data](https://aclanthology.org/2024.findings-emnlp.853/) | EMNLP 2024 Findings；数据 RolePersonality | **M** | 沿用 InCharacter 的十四类量表访谈生成并过滤人格指示训练数据，同底座、约等量数据对照支持人格指标与动机选择题改善；并非十四种等价心理构念，也不是自主行动或真实内在心智的证明。 |
| RP-012 | [RoleAgent: Building, Interacting, and Benchmarking High-quality Role-Playing Agents from Scripts](https://papers.nips.cc/paper_files/paper/2024/hash/5875aca1ef70285a35940afbbce0f9fb-Abstract-Datasets_and_Benchmarks_Track.html) | NeurIPS 2024 Datasets and Benchmarks Track | **M** | 从剧本构建 observation—event—keypoint—insight 分层记忆，再组织自我、他人、关系和意图推断；RoleAgentBench 支持离线知识与回应测量，不能据此证明开放社会持续演化。 |
| RP-013 | [CoSER: Coordinating LLM-Based Persona Simulation of Established Roles](https://proceedings.mlr.press/v267/wang25dk.html) | ICML 2025 | **M** | 从 771 本书提取人物场景、对白、动作与内心活动，训练共享角色模型并提出 GCA 复演评测；部分心理活动由教师推断，最多二十轮的文本复演不等于真实游戏执行，后续改变 judge 的分数不可直接拼榜。 |
| RP-014 | [Beyond Dialogue: A Profile-Dialogue Alignment Framework Towards General Role-Playing Language Model](https://aclanthology.org/2025.acl-long.586/) | ACL 2025 Main | **M** | 以角色、风格、情绪、关系和人格标签对齐 profile 与对白，再混合对齐任务训练；同规模数据对照支持设定一致性监督的价值，短场景与教师标签不能验证长期心理真实性。 |
| RP-015 | [OpenCharacter: Training Customizable Role-Playing LLMs with Large-Scale Synthetic Personas](https://arxiv.org/abs/2501.15427v2) | arXiv v2（2025-02-18）；未核实正式 venue | **M** | 从 PersonaHub 扩展约两万原创角色并合成角色化指令数据，提供区别于知名人物模仿的训练路线；PersonaGym 全集与 Light 子集结论不同，改善主要集中于部分维度，不能概称全面超过强闭源模型。 |
| RP-016 | [Identifying and Mitigating Bottlenecks in Role-Playing Agents: A Systematic Study of Disentangling Character Profile Axes](https://aclanthology.org/2026.emnlp-main.1590/) | EMNLP 2026 Main；FACD | **M** | 在信息量匹配的 211 个人设上拆分熟悉度、结构和道德倾向，提出字段级对比解码；结果受丰富设定、模型和任务条件约束，不能推断结构或熟悉度普遍无关，安全子测也不是对抗保证。 |
| RP-017 | [Quantifying and Optimizing Global Faithfulness in Persona-driven Role-playing](https://proceedings.neurips.cc/paper_files/paper/2024/hash/309cadc33589efca4018a490c07db263-Abstract-Conference.html) | NeurIPS 2024 Main；APC | **M** | 区分应体现的主动设定与不得违反的被动设定，用相关性/NLI 分数筛选偏好做 DPO；已核正文及评分训练代码，平均忠实度改善不构成严格 MAX-CSP 求解或全局不崩塌保证。 |
| RP-018 | [TimeChara: Evaluating Point-in-Time Character Hallucination of Role-Playing Large Language Models](https://aclanthology.org/2024.findings-acl.197/) | ACL 2024 Findings | **M** | 以未来、在场/不在场和过去事实/错误前提测试点时间幻觉，并用 temporal/spatial experts 与 cutoff-RAG 改善边界；不在场主要检查是否谎称亲历，尚非完整信息传播与错误信念追踪。 |
| RP-019 | [Staying In Character: Perspective-Bounded Memory For Book-Based Role-Playing Agents](https://arxiv.org/abs/2606.25632v1) | arXiv v1（2026-06-24）；REVERIEMEM / KBF-QA | **M** | 结合第一人称 episodic memory、带角色可见性的事实图及情绪表达模式，在 KBF-QA 同时测可知回答与拒知；可见性规则与 benchmark 定义相关，检索过滤不等于清除参数知识或解决多级传闻。 |
| RP-020 | [The Curse of Knowledge in Role-Playing Language Models](https://arxiv.org/abs/2610.17327v1) | arXiv v1（2026-10-12） | **M** | 用仅改变隐藏事实的反事实场景对照区分信息泄漏与猜测，比较自报可知性、语言及搜索行为；过滤到角色观察视图有效但依赖正确权限元数据，文本描述的听看测试不是实际感知实验，也非所有模型普遍失败。 |
| RP-021 | [RoleMRC: A Fine-Grained Composite Benchmark for Role-Playing and Instruction-Following](https://aclanthology.org/2025.findings-acl.1082/) | ACL 2025 Findings | **M** | 组合角色专业边界、阅读理解、嵌套格式和多轮优先级规则，并分析 SFT/DPO 激活变化；专业相关性代理不是真实知识边界，局部神经元缩放实验不证明普遍的角色—指令机制分离。 |
| RP-022 | [CHARM: Character Hallucination for Multicultural Role Play Benchmark](https://aclanthology.org/2026.findings-emnlp.460/) | EMNLP 2026 Findings | **B** | 多语言/文化与角色知识幻觉维度；本次仅核原始元数据、摘要及任务范围，不推断未核读的方法细节和资源完备性。 |

<a id="topic-3"></a>
## 3. 人物内心推理、性格、情绪与价值

| 统一论文 ID | 完整题名与入口 | 发表状态 | 阅读 | 方法、证据与适用边界 |
| --- | --- | --- | :---: | --- |
| RP-023 | [R-CHAR: A Metacognition-Driven Framework for Role-Playing in Large Language Models](https://aclanthology.org/2025.emnlp-main.1372/) | EMNLP 2025 Main | **M** | 利用教师评估、重采样与假设扩展构造角色思考数据，再 LoRA SFT 小模型；SocialBench 部分指标提高但风格、短记忆等有退化，“metacognition”首先指数据修订过程，不是已经验证的内在元认知。 |
| RP-024 | [Thinking in Character: Advancing Role-playing Agents with Role-Aware Reasoning](https://papers.nips.cc/paper_files/paper/2025/hash/aacca7b6a20d157112205a44f42821c8-Abstract-Conference.html) | NeurIPS 2025 Main；RAR | **M** | 结合人物情绪、经历、立场和动机的推理蒸馏，以及按场景匹配推理风格的偏好训练；消融支持角色化思考而非单纯增加 thinking tokens，文本推理风格不等于隐性人物状态的可验证机制。 |
| RP-025 | [HER: Human-like Reasoning and Reinforcement Learning for LLM Role-playing](https://aclanthology.org/2026.findings-acl.1283/) | ACL 2026 Findings | **M** | 分离系统思考与第一人称角色思考，结合按样例生成原则的奖励模型进行 RL；SFT、双层思考和 RL 贡献需分开，其 CoSER judge 与思想可见性已改变，不能与原版 CoSER 分数直接比较或视为硬 RLVR。 |
| RP-026 | [Character-R1: Enhancing Role-Aware Reasoning in Role-Playing Agents via RLVR](https://arxiv.org/abs/2601.04611v1) | arXiv v1（2026-01-08）；未核实正式录用记录 | **M** | 用认知焦点标签、属性与参考重叠奖励及角色条件归一化训练角色推理；650 样本上的代理指标改善不表示完整开放式表演具有唯一真值，也不能由异底座对照证明消除了 SFT 机械感。 |
| RP-027 | [VeriRole: Verifiable Role-Awareness through Hint-Guided Reinforcement Learning](https://proceedings.iclr.cc/paper_files/paper/2026/hash/12df08e9280061b4877f97598c644c3e-Abstract-Conference.html) · [补充原始记录／版本](https://arxiv.org/abs/2505.10218) | ICLR 2026；RAIDEN-R1 前序版本并入本条 | **M** | 生成来自 profile/历史的 hint，再以格式、来源、语义及答案反馈优化角色推理；含 embedding 和模型判分，非全部 rule-only，前序 RAIDEN-R1 的知识增益伴边界退化体现平均分掩盖的权衡。 |
| RP-028 | [MECoT: Markov Emotional Chain-of-Thought for Personality-Consistent Role-Playing](https://aclanthology.org/2025.findings-acl.435/) | ACL 2025 Findings | **M** | 将二维情绪环上的离散状态转移与人格、上下文推理结合，提供 RAPD 与情绪一致性度量；情绪分类与模型评分不等于心理机制效度，ETCC 对相关系数平方会丢失方向信息。 |
| RP-029 | [Reasoning Does Not Necessarily Improve Role-Playing Ability](https://aclanthology.org/2025.findings-acl.537/) | ACL 2025 Findings | **T** | 比较直接、CoT 与推理模型在角色任务上的行为；常规长推理可能偏离角色视角，但不是所有思考都降低角色能力的通则。 |
| RP-030 | [Guess What I am Thinking: A Benchmark for Inner Thought Reasoning of Role-Playing Language Agents](https://aclanthology.org/2025.findings-emnlp.819/) | EMNLP 2025 Findings；RoleThink/MIRROR | **T** | 从 76 本书构建 6,058 条角色心理/内心活动条目，区分原文 Gold 与解释性 Silver，MIRROR 组织记忆与反思；部分测试子集不能冒充全库规模。 |
| RP-031 | [EmoCharacter: Evaluating the Emotional Fidelity of Role-Playing Agents in Dialogues](https://aclanthology.org/2025.naacl-long.316/) | NAACL 2025 Main | **T** | 将情绪触发与人物性格、单/多轮转移分开评价，六类指标揭示部分角色强化方式损害情绪忠实；不是心理生理学的客观情感读数。 |
| RP-032 | [When Roleplaying, Do Models Believe What They Say?](https://arxiv.org/abs/2606.11502) | arXiv 2026 预印本 | **T** | 角色假信念、质询与线性 truth probe 的表征/行为关联；probe 不会直接读出模型真实“心理信念”。 |
| RP-033 | [Beyond Static Persona Consistency: Dynamic Persona Coherence in LLM Role-Playing](https://aclanthology.org/2026.acl-long.1336/) | ACL 2026 Main | **T** | 长/中/短时间尺度的稳定身份与动态情绪、PCC/PCR/PDS 校正；少量角色与自设 judge 的增益不能外推为普适心理机制。 |
| RP-034 | [PersonaForge: Psychology-Grounded Dual-Process Architecture for Personality-Consistent Role-Playing Agents](https://aclanthology.org/2026.findings-acl.386/) | ACL 2026 Findings | **T** | 多层心理状态和选择性 inner monologue，关注 50 轮人格保持与开销；公开代码不附有版权人物原文数据。 |
| RP-035 | [ToMATO: Verbalizing the Mental States of Role-Playing LLMs for Benchmarking Theory of Mind](https://ojs.aaai.org/index.php/AAAI/article/view/32143) | AAAI 2025；39(2):1520–1528 | **M** | 将角色合成的私有思想转为 5,401 道一/二阶心理状态问题，测试观察者从完整对话推断他人状态；标签不是实际心智真值，任务不直接评价 NPC 在线决策，作者建议数据仅用于评测，代码受 NTT 非商业研究评估许可约束。 |
| RP-036 | [Too Nice to Tell the Truth: Quantifying Agreeableness-Driven Sycophancy in Role-Playing Language Models](https://aclanthology.org/2026.acl-long.1421/) | ACL 2026 Main | **T** | 275 合成人设、4,950 观点题、13 模型；9 个模型内宜人性与附和正相关，然而多数模型采用 persona 后较无 persona 的整体平均迎合下降。立场分类分数不是人物心理或真假事实的完备真值。 |

<a id="topic-4"></a>
## 4. 训练、奖励建模与多轮优化

| 统一论文 ID | 完整题名与入口 | 发表状态 | 阅读 | 方法、证据与适用边界 |
| --- | --- | --- | :---: | --- |
| RP-037 | [CPO: Addressing Reward Ambiguity in Role-playing Dialogue via Comparative Policy Optimization](https://aclanthology.org/2025.findings-emnlp.18/) | EMNLP 2025 Findings | **M** | 用组内候选分析、排序和评分缓解开放式角色奖励的绝对分噪声；支持同底座上有限平均改善，RL 与 CharacterArena 的角色重叠、组内组成效应和主观 judge 仍限制泛化解释。 |
| RP-038 | [Act-Adaptive Margin: Dynamically Calibrating Reward Models for Subjective Ambiguity](https://aclanthology.org/2026.acl-long.710/) · [补充原始记录／版本](https://arxiv.org/abs/2505.23923) | ACL 2026 Main；AAM，前序题名 ChARM | **M** | 以动态 margin 和 SFT 正则校准主观偏好奖励，并在 Charm 数据和角色优化中验证；与旧版 ChARM 及相关数据名称按同一论文发展链计数，收益不代表奖励评审已经客观无偏。 |
| RP-039 | [CRPO: Character-centric Group Relative Policy Optimization for Role-aware Reasoning in Role-playing Agents](https://proceedings.mlr.press/v306/tang26c.html) | ICML 2026 | **M** | 分别处理任务组内优势和角色级风格优势，结合熵调节与通用回答负 anchor；同规模算法对照支持特定代理奖励下的改善，不能外推为普遍角色目标分解或与异规模 HER 直接比较。 |
| RP-040 | [MOA: Multi-Objective Alignment for Role-Playing Agents](https://aclanthology.org/2026.acl-long.531/) | ACL 2026 Main | **M** | 通过动态目标权重、pivot 与冲突样本筛选对齐对话、角色知识和风格，并加入思考和 off-policy 指导；需要分离各组件贡献，学习型 judge 与局部理论假设不支持全局 Pareto 最优保证。 |
| RP-041 | [Consistently Simulating Human Personas with Multi-Turn Reinforcement Learning](https://papers.nips.cc/paper_files/paper/2025/hash/4c91443877f8388d8190c938ac5a4d4d-Abstract-Conference.html) | NeurIPS 2025 Main | **M** | 对学生、来访者和聊天用户模拟进行多轮 PPO，以 profile-to-line、line-to-line 和问答探测评价一致性；静态身份保持的收益不等于真实人群行为效度，也可能惩罚合理信念与情绪变化。 |
| RP-042 | [Agentic Reinforcement Learning with Implicit Step Rewards](https://openreview.net/forum?id=ooROvpmxMV) · [补充原始记录／版本](https://arxiv.org/abs/2509.19199v3) | ICLR 2026；iStar；核读 arXiv v3 | **M** | 从轨迹偏好学习隐式过程奖励，再组合步骤与整段优势；角色相关证据来自 SOTOPIA 社交目标，WebShop 或推箱子的客观成功不能用来证明社会奖励或人物忠实度可验证。 |
| RP-043 | [Long-Short Horizon Reinforcement Learning for Persona-Level Role-Playing Agents](https://aclanthology.org/2026.findings-emnlp.1619/) | EMNLP 2026 Findings；LSH-RL | **M** | 以局部质量门控角色轨迹奖励，结合 DPO warm-start、对话 RL 和动作细化；PersonaArena/CharacterBox 支持文本互动的长短期目标协调，不证明 3D 引擎动作执行或普遍胜过 episode-only RL。 |
| RP-044 | [OSPD: On-Policy Self-Distillation for Persona-Consistent Dialogue](https://aclanthology.org/2026.emnlp-main.2105/) | EMNLP 2026 Main | **M** | 让完整人设 EMA 教师在学生短人设生成轨迹上蒸馏，并按熵选择 KL 方向、逐步遮蔽属性；证据针对 brief-profile 部署，默认 verifier 仍依赖外部模型，公开参考实现不含论文完整数据、评测包和权重。 |
| RP-045 | [KuaiRP Series Role-playing Models Technical Report](https://arxiv.org/abs/2609.11127v1) | arXiv v1（2026-09-10）；Kuaishou GameMind Lab 技术报告 | **M** | 报告特定小说世界的角色数据、格式/重复奖励及能力保持蒸馏，展示角色专门化与通用工具能力的权衡；局限于少量域内人物和内部评价，未核到完整开源模型、训练数据或代码。 |
| RP-046 | [DynSess: Dynamic Session-Level Evaluation and Optimization Framework for Role-Playing Agents](https://aclanthology.org/2026.findings-emnlp.689/) | EMNLP 2026 Findings | **M** | 以整段互动 rubric、前瞻轨迹搜索和 DSPO/GSRPO 优化会话质量；默认评价是在不同长度前缀后续写短段，学得 judge 奖励不是硬真值，自动分与人类偏好改善幅度也不相同。 |
| RP-047 | [R4: Nested Reasoning-Retrieval for Reward Modeling in Role-Playing Agents](https://openreview.net/pdf?id=sWQSbVsPEz) | ICLR 2026 | **T** | R4 在 reward model 与对话策略两侧加入角色知识检索和结构化推理。定点核实 Table 3 消融：完整版本 Character Consistency 64.64；去 RM 推理 49.87、去 agent 推理 56.94；Generic Retrieval 47.95 低于 RM 无检索 58.31。结论限定于论文内模型和评价协议，不能泛化为所有 RM 架构均更重要。训练/权重资源仍待核。 |
| RP-048 | [RoleRMBench & RoleRM: Towards Reward Modeling for Profile-Based Role Play in Dialogue Systems](https://arxiv.org/abs/2512.10575) | arXiv 2025 预印本 | **T** | 七类角色偏好子任务与 CIP/候选排序奖励，评估泛用 RM 失配；本论文设置中最高分不代表开放式人物真值，完整更新权重尚待发布。 |

<a id="topic-5"></a>
## 5. 记忆、时间、关系与角色弧线

| 统一论文 ID | 完整题名与入口 | 发表状态 | 阅读 | 方法、证据与适用边界 |
| --- | --- | --- | :---: | --- |
| RP-049 | [Towards Lifelong Dialogue Agents via Timeline-based Memory Management](https://aclanthology.org/2025.naacl-long.435/) | NAACL 2025 Main；THEANINE | **M** | 把事件记忆组织为时间线和关系，在回答时检索并细化相关演变链；三至五会话和 TeaFarm 支持保留变化过程，但不代表所有历史无损，也不直接验证虚构人物长期关系演化。 |
| RP-050 | [BOOKMARKS: Checkpoint-Accelerated Active Grounding for Role-Playing](https://arxiv.org/abs/2605.14169v2) | arXiv v2（2026-09-26）；题名较初版已更新 | **M** | 按场景复用或创建 concept/state/behavior bookmark，仅同步其上次位置以来的叙事后缀；增量成本与原作动作预测得到测试，Best@3 仍含事后选优，不能等同分支游戏中的单次自主行动。 |
| RP-051 | [From Facts to Insights: A Persona-Driven Dual Memory Framework and Dataset for Role-Playing Agents](https://aclanthology.org/2026.findings-emnlp.270/) | EMNLP 2026 Findings；RoleMemo / DualMem | **M** | 分别写入事实与带证据链接的人格条件 insight，并用 RoleMemo 和 writer RL 检验主观解释记忆；逆向合成数据和共享 judge 限制外部效度，公开代码不等于完整数据与 RL agent 已发布。 |
| RP-052 | [ArcANE: Do Role-Playing Language Agents Stay in Character at the Right Time?](https://aclanthology.org/2026.emnlp-main.1998/) · [补充原始记录／版本](https://arxiv.org/abs/2606.05553v2) | EMNLP 2026 Main；核读 arXiv v2（2026-09-02） | **M** | 在同一人物不同叙事 phase 下询问相同场景，区分动作、理由与轨迹方向，并用相邻错误阶段作偏好负例；角色弧线忠实不等于在线双向关系成长，逐阶段奖励提升也不保证整体轨迹改善。 |
| RP-053 | [DREAM: LLM-based Dynamic Role-playing via Event-Aware Memory Graph](https://doi.org/10.1145/3770855.3818027) · [补充原始记录／版本](https://arxiv.org/abs/2608.05170) | KDD 2026 Main | **M** | 从已完成小说构建事件、时间和叙事因果图，在当前节点生成动态 profile；TCM 与角色评测支持离线时间定位，新增互动的在线图更新仍属未来工作，pairwise 胜率不是绝对边界准确率。 |
| RP-054 | [PersMem: Internalizing Personality into Dual-Pathway Memory for LLM Agents](https://arxiv.org/abs/2609.34372v1) | arXiv v1（2026-09-28） | **M** | 将预定义人格映射到情绪评价、保留与被动/主动检索参数，测量依恋和 Big Five 条件下的行为差异；手工校准、短对话及小规模配对限制心理外推，引用旧 CoSER 分数不是同 judge 的公平 SOTA 比较。 |
| RP-055 | [REMP: A Structured Event-Probing Benchmark for Long-Horizon Role-Playing Dialogue](https://aclanthology.org/2026.findings-emnlp.602/) | EMNLP 2026 Findings | **M** | 以关系、情绪、记忆和人格四维事件锚点评价长历史后的诊断分支；约八百轮是预制背景长度，不是被测模型完整自由 rollout，当前公开样例也不能当作已释放全八十轨迹。 |
| RP-056 | [Memory-Driven Role-Playing: Evaluation and Enhancement of Persona Knowledge Utilization in LLMs](https://aclanthology.org/2026.findings-acl.1175/) | ACL 2026 Findings；MRBench / MRPrompt | **M** | 拆分 anchoring、selecting、bounding、enacting，比较同内容不同 persona schema 与推理提示；输入中的记忆不是直接测参数记忆，给定历史的下一回复也不等于外部记忆写入或长程状态维护。 |
| RP-057 | [StratMem-Bench: Evaluating Strategic Memory Use in Virtual Character Conversation Beyond Factual Recall](https://aclanthology.org/2026.acl-long.1491/) | ACL 2026 Main | **M** | 在固定记忆池内区分必要、可选和无关信息，测选择完整性与自然融入；judge 检测后规则聚合仍依赖语义评判，结果只支持 read/use 能力，不能推出存储、检索和遗忘质量。 |
| RP-058 | [SubtleMemory: A Benchmark for Fine-Grained Relational Memory Discrimination in Long-Horizon AI Agents](https://aclanthology.org/2026.findings-emnlp.1199/) | EMNLP 2026 Findings | **M** | 以互补、情境差异和矛盾事实检验顺序写入、检索及生成，并用 oracle 诊断瓶颈；这里 relational 指事实关系，固定历史 replay 的单次回答不衡量人际关系、人格或在线情绪演化。 |
| RP-059 | [PsyMem: Fine-grained Psychological Alignment and Explicit Memory Control for Advanced Role-Playing LLMs](https://aclanthology.org/2026.tacl-1.24/) | TACL 2026 | **T** | 用 26 个心理指标和显式 memory-alignment 训练角色行为，论文包含 5,414 个角色和 38,962 段小说对话。它不是仅用 RAG 召回、也不等于长周期玩家关系学习；本次仅定点核读，资源发布未完整审计。 |
| RP-060 | [If an LLM Were a Character, Would It Know Its Own Story? Evaluating Lifelong Learning in LLMs](https://aclanthology.org/2026.acl-long.1659/) | ACL 2026 Main；LifeState-BENCH | **T** | Hamlet 与合成分幕剧情的经历、自我与关系状态追踪；静态历史或有序事件 probe 不等于真实玩家生命周期的在线参数学习。 |
| RP-061 | [Persistent Personas? Role-Playing, Instruction Following, and Safety in Extended Interactions](https://aclanthology.org/2026.eacl-long.246/) | EACL 2026 Main | **M** | 比较访谈与目标任务中百轮级历史下的人格淡化、指令遵循和安全变化；人设趋向无 persona 基线可伴随拒答增加，不能将这种副作用当作角色与安全同时改善。 |
| RP-062 | [LIFELONG-SOTOPIA: Evaluating Social Intelligence of Language Agents over Lifelong Social Interactions](https://arxiv.org/abs/2506.12666v1) | arXiv v1（2025-06-14）；未核实正式 venue | **M** | 用固定角色对跨四十个 episode 的历史研究长期社会目标与关系条件化；随机目标未必需要历史，少量人工依赖任务才更直接暴露记忆不足，专属数据与代码未确认完整公开。 |

<a id="topic-6"></a>
## 6. 符号、参数、激活、解码与架构控制

| 统一论文 ID | 完整题名与入口 | 发表状态 | 阅读 | 方法、证据与适用边界 |
| --- | --- | --- | :---: | --- |
| RP-063 | [Codifying Character Logic in Role-Playing](https://papers.neurips.cc/paper_files/paper/2025/file/15294ba2dcfb4521274f7aa1c26f4dd4-Paper-Conference.pdf) | NeurIPS 2025 Main；核读正式版 | **M** | 将人物设定编译为带条件查询的可执行函数，拆分离线编译与在线生成；八十三角色场景预测支持结构化逻辑的效用，更新实验借助参考动作、Best@K 借助事后选择，不能等同自主演化与单次决策质量。 |
| RP-064 | [Deriving Character Logic from Storyline as Codified Decision Trees](https://aclanthology.org/2026.acl-long.568/) | ACL 2026 Main；CDT | **M** | 从场景—动作实例聚类、提出条件规则并以 NLI 验证，递归构造可解释决策树；测的是原作动作预测，语义条件仍由模型判断，静态离线树不构成心理机制或在线更新的形式化保证。 |
| RP-065 | [Neeko: Leveraging Dynamic LoRA for Efficient Multi-Character Role-Playing Agent](https://aclanthology.org/2024.emnlp-main.697/) | EMNLP 2024 Main | **M** | 用角色 profile 门控动态 LoRA 子块，并通过 fusion/expansion 支持角色共享及增量加入；九角色和 8+1 设置验证参数复用，未彻底消除角色串扰，也未验证千角色并发部署。 |
| RP-066 | [Impatient Users Confuse AI Agents: High-fidelity Simulations of Human Traits for Testing Agents](https://aclanthology.org/2026.acl-long.1743/) | ACL 2026 Main；TraitBasis / τ-Trait | **M** | 以对比样本激活差向量控制四类用户特征，评估客服工具智能体对非理想用户的鲁棒性；不是 SAE，有限特征组合不证明任意文学人格可连续独立控制，默认服务还依赖 STEER API。 |
| RP-067 | [Codified Finite-State Machines for Role-playing](https://proceedings.iclr.cc/paper_files/paper/2026/hash/a862f5788fd09bb6843c694d8120d50c-Abstract-Conference.html) · [全文 HTML](https://arxiv.org/html/2602.05905v1) | ICLR 2026 | **M** | 从 profile 抽取关键心理/叙事状态及事件条件，用 LLM 编译可执行状态转移；CPFSM 加入状态概率。已知简化 FSM 的确定执行测试、Fandom 参考动作 NLI 与 Best@K 分别衡量不同方面；不是引擎动作验收或人物真实心理真值。直接连接 2025 Codified Profile 与 2026 CDT，但研究对象是**状态转移**，不能省略。 |
| RP-068 | [PERSONA: Dynamic and Compositional Inference-Time Personality Control via Activation Vector Algebra](https://proceedings.iclr.cc/paper_files/paper/2026/hash/f66ce276436c4cd151535b03841ac713-Abstract-Conference.html) | ICLR 2026 | **T** | 对比激活特质向量、动态缩放/组合和 Persona-Evolve；可组合的行为效果不证明人格维度严格独立。 |
| RP-069 | [Enhancing Persona Following at Decoding Time via Dynamic Importance Estimation](https://arxiv.org/abs/2603.01438) | ICLR 2026，PDD | **T** | 根据当前上下文估计人设属性相对重要性，并在 token 解码时对比分布；优化目标的等号条件不是人物心理真实度定理。 |
| RP-070 | [Facet-Level Persona Control by Trait-Activated Routing with Contrastive SAE for Role-Playing LLMs](https://arxiv.org/abs/2602.19157) | arXiv 2026 预印本 | **T** | Big Five facet 对比数据、SAE 潜变量和情境路由；它与普通残差激活方向不是同一方法，公开完整训练/权重未核定。 |
| RP-071 | [Know Thyself, Know Thy User: Intrinsic Dual-Perspective Reasoning for Role-Playing LLMs](https://proceedings.mlr.press/v306/sun26at.html) | ICML 2026；KSKT | **T** | Transformer self-role 与 other-user 两路条件融合，直接刻画人物立场与玩家需求之间的张力；示例代码不意味着完整训练权重已发布。 |

<a id="topic-7"></a>
## 7. 评价、玩家输入、自然度与安全

| 统一论文 ID | 完整题名与入口 | 发表状态 | 阅读 | 方法、证据与适用边界 |
| --- | --- | --- | :---: | --- |
| RP-072 | [InCharacter: Evaluating Personality Fidelity in Role-Playing Agents through Psychological Interviews](https://aclanthology.org/2024.acl-long.102/) | ACL 2024 Main | **M** | 将十四类量表改成开放访谈，以隔离上下文、匿名化和不同映射方式评估人物人格忠实度；金标准包含读者投票与解释，量表吻合不是临床人格或情境行为真实性。 |
| RP-073 | [CharacterEval: A Chinese Benchmark for Role-Playing Conversational Agent Evaluation](https://aclanthology.org/2024.acl-long.638/) | ACL 2024 Main；CharacterRM | **M** | 提供中文文学人物多维回复评测、人类标注与 CharacterRM；主要测固定历史下下一回复，按 example 划分可能共享原对话，奖励模型未被证明消除长度偏差或适用于所有人物价值观。 |
| RP-074 | [Beware of Your Po! Measuring and Mitigating AI Safety Risks in Role-Play Fine-Tuning of LLMs](https://aclanthology.org/2025.acl-long.544/) | ACL 2025 Main；SaRFT | **M** | 测量角色 SFT 的安全退化，并对风险代理选中的样本加强相对安全底座的约束；拒答率及有限 RoleBench 指标支持折中改善，不能称安全底线被锁死或所有沉浸体验无损。 |
| RP-075 | [Knowing-but-Doing: Diagnosing and Defending Role-Play-Driven LLMs Jailbreaks via Moral Disengagement](https://aclanthology.org/2026.findings-acl.349/) | ACL 2026 Findings；MD-Trace / MD-Shield | **M** | 拆分任务、人物和情境压力，观察风险识别文本与危险遵从并存，再训练角色内安全回应；可见 reasoning 不是内部道德心理的直接证据，静态攻击效果不等于长期防护保证。 |
| RP-076 | [PersonaGym: Evaluating Persona Agents and LLMs](https://aclanthology.org/2025.findings-emnlp.368/) | EMNLP 2025 Findings | **M** | 对二百个人设在环境适应、人格一致等五类任务生成一万问题，并用 ensemble 与示例化 rubric 评价；动态生成题目不等于长期自由交互，模型规模与得分关系仅对该任务和 judge 成立。 |
| RP-077 | [RAIDEN Benchmark: Evaluating Role-playing Conversational Agents with Measurement-Driven Custom Dialogues](https://aclanthology.org/2025.coling-main.735/) | COLING 2025 Main | **M** | 由标注者针对十一维构建 135 角色多轮对话，采用固定历史续写和成对 RPCAJudger；不是全程自由互动，105 个训练角色资料与三十个公开测试角色的资源范围需区分。 |
| RP-078 | [FURINA: A Fully Customizable Role-Playing Benchmark via Scalable Multi-Agent Collaboration Pipeline](https://arxiv.org/abs/2510.06800v3) | arXiv，首发 2025；核读 v3（2026-04-06），未核实正式 venue | **M** | 通过多智能体构造可指定人物、情境与指标的评测数据，覆盖已知/原创及中英角色；实际评价为固定历史下一句，模型样本上的性能—幻觉权衡不是普遍 Pareto 定理或闭环多人社会证明。 |
| RP-079 | [DMT-RoleBench: A Dynamic Multi-Turn Dialogue Based Benchmark for Role-Playing Evaluation of Large Language Model and Agent](https://ojs.aaai.org/index.php/AAAI/article/view/34768) | AAAI 2025；39(24):25760–25768 | **M** | 以 996 个中文种子驱动闭环多轮访谈，用十四维 DMT-RM/DMT-Score 评价保持能力；多数维度采用前缀一错全错，曲线下降部分来自定义，官方仓库仍未核到种子与评测器的实际发布。 |
| RP-080 | [RoleCDE: Benchmarking and Mitigating Role–Alignment Trade-offs in Role-Playing Agents](https://aclanthology.org/2026.findings-acl.106/) | ACL 2026 Findings；以正式 PDF 为准 | **M** | 用 7,957 个 profile–scenario 组合、23,871 个两选项 dilemma 测三种难度下角色与默认对齐的取舍；DBR 不是越高越好，人评边际分布接近不等于逐例一致，SFT/DPO 有通用指标损失；[作者仓库](https://github.com/rabbitrose/RoleCDE)已核 986 个 persona JSON 及训练／评价代码，公开子集不等于论文全池，未见权重、未执行复现。 |
| RP-081 | [RMTBench: Benchmarking LLMs Through Multi-Turn User-Centric Role-Playing](https://aclanthology.org/2025.findings-emnlp.730/) | EMNLP 2025 Findings | **M** | 从玩家/用户目的而非原作人物知识出发，80 个角色、8,156 条中英话语；覆盖人物探查、人设坚持、隐含意图、偏好和敏感试探。用户发言固定，角色从首轮起自行生成前轮回复，介于静态续写与完全双向闭环之间；judge 依赖模型且部分维度校准有限。 |
| RP-082 | [MCPDial: A Minecraft Persona-driven Dialogue Dataset](https://arxiv.org/abs/2410.21627) | arXiv 首发 2024，正式 venue 未核实 | **T** | 将玩家—NPC 双侧 persona、长对话及话语之间的函数调用组合为合成监督数据，仓库已见训练/测试 JSON。函数调用标注没有引擎执行回执，不能称闭环行为成功。 |
| RP-083 | [Fake Player: Imitating Real Player to Distill Data for LLM-based NPC Training](https://openreview.net/pdf/2e26df077644bbbe3df13f485ea6433e09764b7b.pdf) | 匿名 ICLR 2026 投稿稿，未核正式录用 | **B** | 内心独白、意图栈和打字行为模拟玩家侧受限表达，并使用 Distill Bench 比较数据。明确提出玩家输入分布问题；模拟数据效果不等于已测真实玩家行为，完整发布与身份未核定。 |
| RP-084 | [Quest of Aivengarde: Comparative Study of Player Experience Across LLM Dialogue Systems](https://portal.findresearcher.sdu.dk/en/publications/quest-of-aivengarde-comparative-study-of-player-experience-across/) | FDG 2026 发表记录 | **B** | 对比 RPG 中静态、改写、混合和完全生成式 NPC 对话，64 位参与者的日志与问卷衡量开放性和体验。仅核正式摘要及元数据，未完整阅读实验，不能将“更长对话”自动解释为更忠实的人物。 |
| RP-085 | [Deflanderization for Game Dialogue: Balancing Character Authenticity with Task Execution in LLM-based NPCs](https://arxiv.org/html/2510.13586) | 2025 arXiv 预印本、CPDC 参赛报告 | **M** | 简洁且不夸张的 fantasy RPG 角色提示，与 few-shot、CoT、函数提示和 Qwen3-14B LoRA 共同研究功能性回应与人物自然度。部分组合的比赛收益不证明 GRPO/DPO 普遍导致脸谱化或真实人格被形式化。 |
| RP-086 | [PersonaArena: Dynamic Simulation for Evaluating and Enhancing Persona-Level Role-Playing in Large Language Models](https://aclanthology.org/2026.findings-acl.471/) | ACL 2026 Findings | **T** | 从社会材料生成 persona bank 和多轮情境，使用多评审提供角色反馈；多 agent 在这里是评审方法，不是 NPC 合作研究，模拟角色与真人玩家的效度需分别理解。 |
| RP-087 | [CharacterBench: Benchmarking Character Customization of Large Language Models](https://ojs.aaai.org/index.php/AAAI/article/view/34806) | AAAI 2025 | **T** | 3,956 角色/22,859 问题，六组 11 维综合人物评测；CharacterJudge 等配套工具。角色模型的共同参照，不等于全部维度都由独立客观真值评分。 |
| RP-088 | [CharacterBox: Evaluating the Role-Playing Capabilities of LLMs in Text-Based Virtual Worlds](https://aclanthology.org/2025.naacl-long.323/) | NAACL 2025 Main | **T** | 角色 agent 在 narrator 驱动世界中选择行为与对白，另以 CharacterNR/CharacterRM 评价轨迹；LLM narrator 与可验证真实引擎要区分。 |
| RP-089 | [Rethinking Role-Playing Evaluation: Anonymous Benchmarking and a Systematic Study of Personality Effects](https://aclanthology.org/2026.sigdial-1.15/) | SIGDIAL 2026 | **T** | 匿名人物名字，保留描述并测试预训练知名度依赖；匿名化同时会删除合法语境线索，下降并不一概是作弊。 |
| RP-090 | [Too Good to be Bad: On the Failure of LLMs to Role-Play Villains](https://aclanthology.org/2026.findings-acl.282/) | ACL 2026 Findings | **T** | Moral RolePlay 的价值倾向人物测试，揭示部分模型易同化为亲社会助手；无法凭均分将原因全部归给 safety alignment。 |
| RP-091 | [Beyond Borrowed Histories: Person-Aligned User Simulation for Interactive Role-Playing Evaluation](https://arxiv.org/abs/2607.27816) | arXiv 2026 预印本；PALATE | **T** | 116 真人会话、5 个用户模拟 LoRA、约 1,600 条轨迹，研究用户模拟和 persona 评价的对齐；模型用户仍不同于真人。 |

<a id="topic-8"></a>
## 8. 戏剧、社会认知与可执行世界（相邻）

| 统一论文 ID | 完整题名与入口 | 发表状态 | 阅读 | 方法、证据与适用边界 |
| --- | --- | --- | :---: | --- |
| RP-092 | [Learning to Speak and Act in a Fantasy Text Adventure Game](https://aclanthology.org/D19-1062/) | EMNLP-IJCNLP 2019；LIGHT | **M** | 提供有角色、地点、物品 affordance 与状态动作的人类对话环境，连接说话和执行；原评测主要是回复/动作排序预测，不能将其指标直接当现代开放 LLM 的长期任务或人物动机评分。 |
| RP-093 | [Generative Agents: Interactive Simulacra of Human Behavior](https://doi.org/10.1145/3586183.3606763) · [补充原始记录／版本](https://arxiv.org/abs/2304.03442) | UIST 2023 | **M** | 以记忆检索、反思和分层计划驱动二十五角色的小镇，展示日常行动和信息扩散；组件消融采访使用完整系统已有轨迹，不能据此量化移除组件对整段社会发展的因果效应。 |
| RP-094 | [IBSEN: Director-Actor Agent Collaboration for Controllable and Interactive Drama Script Generation](https://aclanthology.org/2024.acl-long.88/) | ACL 2024 Main | **M** | 导演根据剧情与玩家输入给演员发指示，演员维护角色目标、记忆和关系；有限戏剧中的剧情推进支持导演控制，目标完成与文本动作不等于自由玩家能动性或真实引擎状态。 |
| RP-095 | [HAMLET: A Hierarchical and Adaptive Multi-Agent Framework for Live Embodied Theatrics](https://iclr.cc/virtual/2026/poster/10009957) · [补充原始记录／版本](https://arxiv.org/abs/2507.15518v5) | ICLR 2026；核读 arXiv v5 | **M** | 分离离线剧目蓝图、在线规划/推进/叙述及快慢思考和沉默策略；道具动作由 narrator 判断，PAD 的 0.36 秒不等于全系统延迟，动作类未纳入部分量化评价且公开训练资产仍不完整。 |
| RP-096 | [AdaMARP: An Adaptive Multi-Agent Interaction Framework for General Immersive Role-Playing](https://aclanthology.org/2026.findings-acl.1563/) | ACL 2026 Findings | **M** | 用 Scene Manager 管理换场、说话者、角色加入和终止，配合 thought/action/environment/speech 交互数据；推进了动态场景与演员组织，但文本环境及二十轮评价不代表真实物理世界或长期 campaign。 |
| RP-097 | [SocialBench: Sociality Evaluation of Role-Playing Conversational Agents](https://aclanthology.org/2024.findings-acl.125/) | ACL 2024 Findings | **M** | 区分个体角色能力与群体情境中的社会偏好，测试知识、风格、情绪和记忆；大量任务是静态群体上下文选择题或召回题，不能据此宣布 NPC 在线长期互动必然人格同化。 |
| RP-098 | [SOTOPIA: Interactive Evaluation for Social Intelligence in Language Agents](https://proceedings.iclr.cc/paper_files/paper/2024/hash/b3075b88e583a0e98d8b24338a613060-Abstract-Conference.html) · [补充原始记录／版本](https://arxiv.org/abs/2310.11667) | ICLR 2024 | **M** | 以双人角色、私有目标和七维评价构建交互式社会情境；目标得分受伙伴与 judge 影响，动作大体以文本表示，社会目标成功不能代替文学角色忠实或物理执行。 |
| RP-099 | [SOTOPIA-π: Interactive Learning of Socially Intelligent Language Agents](https://aclanthology.org/2024.acl-long.698/) | ACL 2024 Main | **M** | 结合专家行为克隆和自生成轨迹筛选后 SFT 学习社会策略；self-reinforcement 不是在线 policy-gradient/RLVR，自动评分增益与人评差距提示优化 judge 的风险。 |
| RP-100 | [SOTOPIA-Ω: Dynamic Strategy Injection Learning and Social Instruction Following Evaluation for Social Agents](https://aclanthology.org/2025.acl-long.1203/) | ACL 2025 Main | **M** | 在教师数据生成中动态注入谈判策略和阶段目标，再训练学生，增加复读与目标相关性评价；慢思考主要在数据阶段，不能推断学生在线成本或用自动目标分替代真人社交质量。 |
| RP-101 | [SOTOPIA-TOM: Evaluating Privacy and Information Management in Multi-Agent Interaction with Theory of Mind](https://arxiv.org/abs/2605.02307v2) · [补充原始记录／版本](https://proceedings.colm.cc/paper_files/paper/2026) | COLM 2026；核读 arXiv v2（2026-09-08） | **M** | 以公开/私聊可见性、分享政策和多方任务测信息路由，并比较 ToM 提示与显式信念状态；证据侧重职业协调中的隐私—效用权衡，不等于小说人物误信念或完整社会心理模拟。 |
| RP-102 | [Project Sid: Many-agent simulations toward AI civilization](https://arxiv.org/abs/2411.00114v1) | arXiv v1（2024-10-31）技术报告；未核实正式 venue | **M** | 用 PIANO 并发认知模块和 Minecraft 动作接口研究大规模协调、传播与制度内行为；法律/税制等有预设、超千 agent 运行会失稳，报告与展示仓库不等于已公开运行器或从零制度发明。 |
| RP-103 | [Setting the DC: Tool-Grounded D&D Simulations to Test LLM Agents](https://openreview.net/pdf?id=3Op7kJOvaD) · [补充原始记录／版本](https://genprocc.github.io/) | NeurIPS 2025 GenProCC Workshop；非主会 | **B** | 官方摘要提出以规则与工具驱动的 D&D 战斗评价工具使用、参数、表演、战术、状态和效率；PDF 访问受阻，仅核正式工作坊与摘要，不能借 2026 年新闻替代全文效果证据。 |
| RP-104 | [CriticaLLM: Using LLMs as Autonomous Game Master for Tabletop Role-Playing Games](https://arxiv.org/abs/2610.21525v1) | arXiv v1（2026-10-15） | **M** | 将简化桌游规则、地图、骰子和局部记忆接入自主 GM，测试叙事与对抗请求；三房间冒险和九名资深玩家的证据有限，选择影响感偏弱，不能说明通用长篇 GM 已成熟。 |
| RP-105 | [Can LLM Agents Stick to the Script? A Benchmark for Long-Horizon Consistency in Interactive Narratives](https://proceedings.mlr.press/v306/ma26ap.html) | ICML 2026 | **T** | NCP-Bench 将 100 个叙事环境的初始事实、承诺和轨迹与模拟玩家干扰连起来；作者公开数据、评测 runner 和基线。被测对象是 narrator 而非受部分观察限制的单个 NPC；事实/承诺冲突部分由模型审计，不是引擎硬状态奖励。 |
| RP-106 | [Bayesian Social Deduction with Graph-Informed Language Models](https://aclanthology.org/2026.acl-long.1497/) | ACL 2026 Main | **T** | 以因子图跟踪 Avalon 隐藏身份，LLM 处理语言和发言，受控真人试验报告 67% 胜率。实验 agent **只扮演 Good 阵营**，所以不是反派欺骗型角色表演的直接证据。其对 RP 的意义是角色自己的信念、私有信息与策略性语言怎样分离。 |

<a id="topic-9"></a>
## 9. 多模态角色感知、语音与表达

| 统一论文 ID | 完整题名与入口 | 发表状态 | 阅读 | 方法、证据与适用边界 |
| --- | --- | --- | :---: | --- |
| RP-107 | [MMRole: A Comprehensive Framework for Developing and Evaluating Multimodal Role-Playing Agents](https://proceedings.iclr.cc/paper_files/paper/2025/hash/a5c7206fd66e8314bb21a04492359353-Abstract-Conference.html) · [补充原始记录／版本](https://arxiv.org/abs/2408.04203) | ICLR 2025 | **M** | 提供角色—图像—对话数据、模型和多维奖励评审，考察视觉理解与角色反应的一致；主要是静态图片和给定历史目标回复，不能等同连续视觉感知、角色实际视野或具身行动。 |
| RP-108 | [Video2Roleplay: A Multimodal Dataset and Framework for Video-Guided Role-playing Agents](https://aclanthology.org/2025.emnlp-main.1209/) | EMNLP 2025 Main | **M** | 从中文社交媒体视频构造角色对话并训练视频条件模型，探索时间信息和关键帧的价值；离线视频指标与单例多帧耗时不是实时流式互动证据，当前仓库仍有 Coming soon 资源缺口。 |
| RP-109 | [Through the Lens of Character: Resolving Modality-Role Interference in Multimodal Role-Playing Agent](https://arxiv.org/abs/2605.09443v1) | arXiv v1（2026-05-10）；CAVI | **M** | 通过视觉 anchor、低秩投影与角色条件干预缓解视觉—人设竞争；MMRole 上的小规模模型结果和理论假设支持早期探索，不证明普遍可控角色感知，training-free 也不等于无推理成本。 |
| RP-110 | [OmniCharacter: Towards Immersive Role-Playing Agents with Seamless Speech-Language Personality Interaction](https://aclanthology.org/2025.acl-long.1276/) | ACL 2025 Main | **M** | 连接语音理解、角色语言生成和语音输出，提供二十角色语音对话资源与模型；合成语音和同角色测试限制泛化，声线相似与报告的 speech latency 不能代替人格效度和全双工端到端体验。 |
| RP-111 | [OmniCharacter++: Towards Comprehensive Benchmark for Realistic Role-Playing Agents](https://ieeexplore.ieee.org/abstract/document/11506238) · [补充原始记录／版本](https://zchoi.github.io/OmniCharacter-plus/) | IEEE TPAMI 2026；只核元数据与资源 | **B** | 作者扩展到更广角色与场景并公布大型数据和 9B 权重；已核真实 HF 文件，未完成新版主文阅读，不能引用新版详细消融，数据卡与仓库许可描述也需分别核对。 |
| RP-112 | [ActorMind: Emulating Human Actor Reasoning for Speech Role-Playing](https://aclanthology.org/2026.findings-acl.1718/) | ACL 2026 Findings | **M** | 以 Eye/Ear/Brain/Mouth 组织情境情绪推断、同角色语音检索和 TTS；目标台词预先给定，RP-MOS 对错声线直接判最低分，小规模主观评价支持语音表演而非自由对话或行动智能。 |
| RP-113 | [MERRY: Semantically Decoupled Evaluation of Multimodal Emotional and Role Consistencies of Role-Playing Agents](https://arxiv.org/abs/2602.21941) | arXiv 2026 预印本 | **B** | 关注多模态角色感知、情绪与人设的解耦评价；只核摘要与资源声明，不将其列为已核完整评测包。 |

## 10. 消歧、引用和跨文件一致性

| 名称 | 准确对应 |
| --- | --- |
| ChARM / Charm 与 CHARM | RP-038 为 ACL 2026 Main 的 AAM / ChARM（主观奖励 margin、数据集 Charm）；RP-022 为 EMNLP 2026 Findings 的 CHARM（多文化角色幻觉）。**两者完全无关。** |
| PersonaArena 与 LSH-RL | RP-086 为 ACL 2026 Findings 的 PersonaArena 基准，数据和模拟器在 Microsoft 仓库可查；RP-043 为 EMNLP 2026 Findings 的 LSH-RL 算法，使用该基准。LSH-RL 作者未公开的 checkpoint 与 PersonaArena 自身已公开的脚本不冲突。 |
| 名称近似的 Benchmark | RoleBench、RoleMRC、RAIDEN、DMT-RoleBench 任务、split 和评分不同，不是同一套评价。CharacterRM 也须指明是 CharacterEval、CharacterBox 还是其他作者版本。 |
| 表征与推理控制 | NPTI=FFN 神经元，PAS=attention head，PERSONA=残差方向，PDD=token 概率，CV-SAE=稀疏潜表征，KSKT=双流架构；不可统称为 SAE。 |

## 11. 先行控制 Baseline 与外围参考（不计入 113 主论文）

| 外围 ID | 论文与状态 | 在 Role-Play 地图中的位置 |
| --- | --- | --- |
| BASE-NPTI | [Neuron-based Personality Trait Induction in LLMs](https://proceedings.iclr.cc/paper_files/paper/2025/hash/d399b67fa017f0f7670102c88507720c-Abstract-Conference.html)，ICLR 2025；[作者代码](https://github.com/RUCAIBox/NPTI) | 提供 PersonalityBench：**约 18 万条主要用于神经元识别，另约 450 条用于评价**；NPTI 修改 FFN 神经元而非 SAE。 |
| BASE-PAS | [Personality-Activation Search](https://proceedings.iclr.cc/paper_files/paper/2025/file/25203d1cc8c58381eab578f4fcf9c4f8-Paper-Conference.pdf)，ICLR 2025 | 搜索与人格有关的 attention heads、方向与幅度；不同于 NPTI 和残差 steering。 |
| BASE-DPR | [A Systematic Analysis of the Impact of Persona Steering on LLM Capabilities](https://arxiv.org/abs/2604.11048)，CogSci 2026；[代码](https://github.com/cjia7/DPR) | 比较人格 steering 对推理/指令等非目标能力影响，提出 Dynamic Persona Routing。 |
| ADJ-CSP4SDG | [CSP4SDG](https://ojs.aaai.org/index.php/AAAI/article/view/38453)，AAAI 2026 | 不完全信息博弈信念推断的邻接材料，非人物忠实度实验证据。 |
| ADJ-COG25 | [Open-Ended NPC Dialogue Favors Casual Players](https://ieeexplore.ieee.org/abstract/document/11114150)，IEEE CoG 2025 | 与 RP-084 Quest of Aivengarde 玩家研究存在样本/设计延续，不可算两组独立真人实验。 |
| ADJ-FORMAT | [The Price of Format](https://aclanthology.org/2025.findings-emnlp.836/)，EMNLP 2025 Findings | 通用生成格式与多样性相关，不能直接证明 Role-Play RL 必然过度戏剧化。 |

## 12. 工业工程资料（不计入论文）

| 工程 ID | 正式来源 | 与人物扮演的联系 |
| --- | --- | --- |
| IND-01 | [Ubisoft Teammates](https://news.ubisoft.com/it-it/article/3mWlITIuWuu0MoVuR6o8ps/ubisoft-reveals-teammates-an-ai-experiment-to-change-the-game) | 语音队友与作者设定边界，研究演示不等于角色真实性 benchmark。 |
| IND-02 | [NVIDIA ACE Game Agent SDK / Unreal](https://developer.nvidia.com/blog/build-on-device-ai-companions-with-the-nvidia-ace-game-agent-sdk-and-unreal-engine-5-plugins/) | 语音与引擎接口、计算资源约束。 |
| IND-03 | [Inworld Inference](https://inworld.ai/blog/introducing-inworld-inference) | 组件级延迟与模型路由，不能与全双工端到端延迟混比。 |
| IND-04 | [KRAFTON PUBG Ally](https://developer.nvidia.com/blog/how-krafton-built-pubg-ally-a-co-playable-character-powered-by-nvidia-ace/) | 事件语言与高频动作执行接口，不作为个体文学人物忠实度评分。 |

## 13. 阅读与资源审计约束

每条 RP ID 仅出现一次；预印本与正式版合并计数，不能依 venue 名称推断方法正确。论文主张和实际发布的代码、数据、权重分别记录于资源地图。M/T/B 是内容核读范围标记，不是论文质量排名；“实查”也不表示已经下载大文件、运行训练或独立复现。
