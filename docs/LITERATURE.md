# 文献与证据索引

初始文献及资源核验截至 **2026-10-29 UTC**；本轮角色—玩家交互增补核验于 **2026-10-30**。本文件记录本次领域 roadmap 实际使用的论文、阅读层级及证据适用范围，便于区分原论文结论、综述分类和工程实践。它是一份去重后的证据清单，不是按引用数、年份或 venue 排名的推荐书单。

## 1. 阅读层级、去重与统计口径

| 标记 | 本次实际完成的工作 | 不代表什么 |
|---|---|---|
| **M：主文完整阅读** | 研究论文完整阅读主文的问题、方法、实验、分析和局限；综述完整阅读主文分类、论据与局限；按需核读关键附录和作者资源。 | 不表示逐行阅读所有参考文献、所有附录证明，也不表示执行训练或独立复现结果。 |
| **T：定点阅读** | 已阅读全文中的相关章节或指定论点，尚未完成全部主文核读。 | 不计入主文完整阅读数；只用于被实际核查的论点。 |
| **B：元数据／资源核查** | 核对正式发表状态、摘要、作者项目或公开文件；正文未完整取得或未完成阅读。 | 不据此引用未读方法细节、消融或效果结论。 |
| **工程来源** | 阅读官方产品或开发者文章，核对组件、接口与工程口径。 | 不计入论文数，不作为独立同行评审实验或学术效果比较。 |

同一研究的预印本、改名版和正式版合并为一条。年份优先采用正式发表年；没有已核实正式 venue 的工作，采用**首次预印本年份**，所读修订版日期另列。因此，Oscars 的 2025 年修订不将其重算为 2025 年新论文，FURINA 的 2026 年修订也不作为第二篇论文。

| 范围 | 独立论文数 | M：主文完整阅读 | T：定点 | B：元数据／资源 | 其中 2025–2026 年论文 |
|---|---:|---:|---:|---:|---:|
| 原创研究、方法与 benchmark（含技术报告） | 106 | 76 | 23 | 7 | 88／106（83.0%） |
| 综述 | 7 | 6 | 1 | 0 | 4／7（57.1%） |
| **合计** | **113** | **82** | **24** | **7** | **92／113（81.4%）** |

在 82 篇主文完整阅读的论文中，62 篇属于 2025–2026 年，占 75.6%。此次新增 20 篇均按 T/B 登记：17 篇定点阅读、3 篇只核查摘要与元数据，未把针对性核读称为完整主文阅读。原索引列出 **3 篇官方工业文章**，本次再增补 KRAFTON / PUBG Ally 工程访谈，合计 **4 篇工业来源**，均不计入论文数量。上述数字来自下面逐条列出的论文，未把仅检索到、只下载但未审读、或综述参考文献里的论文算进覆盖量。

每条的“贡献与证据范围”同时写出做了什么和实验证明到哪里。表中的 venue 表示已核查的发表记录，**Main、Findings、Datasets and Benchmarks、workshop 和 arXiv 分别标注**；未核实录用的预印本不根据作者宣传或聚合站标签升级为正式顶会论文。

## 2. 综述与领域分类

| ID | 完整题名与原论文入口 | 年份、正式状态或核读版本 | 阅读 | 一句话贡献与证据范围 |
|---|---|---|---|---|
| S01 | [From Persona to Personalization: A Survey on Role-Playing Language Agents](https://openreview.net/forum?id=xrO70E8UIZ) · [补充原始记录／版本](https://arxiv.org/abs/2404.18231v2) | TMLR 2024；核读 arXiv v2（2024-10-09） | **M** | 按 demographic、established character、individualized persona 整理数据、构建与评价，覆盖面超过游戏 NPC；三类是对象差异，不是三个技术代际，产品附录也不能作为 2026 年现状证据。 |
| S02 | [Two Tales of Persona in LLMs: A Survey of Role-Playing and Personalization](https://aclanthology.org/2024.findings-emnlp.969/) · [核读版本](https://arxiv.org/abs/2406.01171v3) | EMNLP 2024 Findings；核读 arXiv v3（2024-10-05） | **M** | 区分赋予模型的人设与适应用户的人设，并整理环境、角色特征和涌现行为；包括专业任务角色与个性化，不能全部归为虚构人物模拟，作者也未建立跨论文统一榜单。 |
| S03 | [The Oscars of AI Theater: A Survey on Role-Playing with Language Models](https://arxiv.org/abs/2407.11484v9) | arXiv，首发 2024；核读 v9（2025-01-10），未核实正式 venue | **M** | 以数据、模型与对齐、智能体架构、评测组织领域，并区分对话质量、人格忠实、行为忠实和吸引力；分类与历史脉络有用，其经验性观点不等于经统一实验确立的普遍定律。 |
| S04 | [Towards a Design Guideline for RPA Evaluation: A Survey of Large Language Model-Based Role-Playing Agents](https://aclanthology.org/2025.findings-acl.938/) | ACL 2025 Findings | **M** | 从 1,676 条初始检索记录筛到 122 篇全文纳入研究，归纳六类智能体属性、七类任务与七类指标；支持评价设计与任务属性对齐，不是 1,676 篇全部深入分析或游戏 NPC 的完整覆盖。 |
| S05 | [Role-Playing Agents Driven by Large Language Models: Current Status, Challenges, and Future Trends](https://arxiv.org/abs/2601.10122v1) | arXiv v1（2026-01-15） | **T** | 从风格、人格、记忆、数据和评价梳理技术发展；仅定点核读相关章节，三代演进是作者叙述框架，不能据此宣布全领域已统一转向认知建模。 |
| S06 | [More Than a Role: Memory in LLM-based Role-Playing Agents](https://github.com/aixiaodewugege/More-Than-a-Role-Memory-in-LLM-based-Role-Playing-Agents) · [补充原始记录／版本](https://pila26-workshop.github.io/) | KDD 2026 PILA Workshop Oral；non-archival，非 KDD 主会 | **M** | 以角色侧和交互侧记忆、承载方式及写入—读取—更新生命周期分析身份保持与关系变化；属于概念综述，未做统一量化元分析，部分二手方法归纳需回到原论文校正。 |
| S07 | [Role Consistency in Role-Playing Agents: A Survey of Evaluation, Memory, Reasoning, Alignment, and Safety](https://aclanthology.org/2026.findings-emnlp.625/) | EMNLP 2026 Findings | **M** | 将角色一致性组织为 specification、role-state、reasoning、alignment、evaluation 的系统性质；benchmark 覆盖表是解释性标注，不能替代性能比较，多模态与具身覆盖仍有限。 |

## 3. 角色数据、设定表示与多角色控制

| ID | 完整题名与原论文入口 | 年份、正式状态或核读版本 | 阅读 | 一句话贡献与证据范围 |
|---|---|---|---|---|
| D01 | [Character-LLM: A Trainable Agent for Role-Playing](https://aclanthology.org/2023.emnlp-main.814/) | EMNLP 2023 Main | **M** | 从人物生平合成经历、情绪与 protective experiences，分别训练九个角色，给出越界回答控制的早期证据；教师同时参与数据和评审，单角色参数训练不证明多角色扩展或长期记忆。 |
| D02 | [RoleLLM: Benchmarking, Eliciting, and Enhancing Role-Playing Abilities of Large Language Models](https://aclanthology.org/2024.findings-acl.878/) | ACL 2024 Findings | **M** | 以 ContextInstruct、RoleGPT 和 RoCIT 构建角色知识与角色化指令监督及 RoleBench，分别评估指令和角色泛化；风格迁移不保证未见角色专属知识，教师评价与知名角色污染仍限制解释。 |
| D03 | [Large Language Models are Superpositions of All Characters: Attaining Arbitrary Role-play via Self-Alignment](https://aclanthology.org/2024.acl-long.423/) | ACL 2024 Main；方法 DITTO | **M** | 用模型自身知识生成 role-specific/role-contrastive 数据进行自对齐，研究角色知识与风格对教师规模的不同依赖；“superposition”是比喻，其边界控制不等于追踪角色时空可知性。 |
| D04 | [Capturing Minds, Not Just Words: Enhancing Role-Playing Language Models with Personality-Indicative Data](https://aclanthology.org/2024.findings-emnlp.853/) | EMNLP 2024 Findings；数据 RolePersonality | **M** | 沿用 InCharacter 的十四类量表访谈生成并过滤人格指示训练数据，同底座、约等量数据对照支持人格指标与动机选择题改善；并非十四种等价心理构念，也不是自主行动或真实内在心智的证明。 |
| D05 | [Quantifying and Optimizing Global Faithfulness in Persona-driven Role-playing](https://proceedings.neurips.cc/paper_files/paper/2024/hash/309cadc33589efca4018a490c07db263-Abstract-Conference.html) | NeurIPS 2024 Main；APC | **M** | 区分应体现的主动设定与不得违反的被动设定，用相关性/NLI 分数筛选偏好做 DPO；已核正文及评分训练代码，平均忠实度改善不构成严格 MAX-CSP 求解或全局不崩塌保证。 |
| D06 | [RoleAgent: Building, Interacting, and Benchmarking High-quality Role-Playing Agents from Scripts](https://papers.nips.cc/paper_files/paper/2024/hash/5875aca1ef70285a35940afbbce0f9fb-Abstract-Datasets_and_Benchmarks_Track.html) | NeurIPS 2024 Datasets and Benchmarks Track | **M** | 从剧本构建 observation—event—keypoint—insight 分层记忆，再组织自我、他人、关系和意图推断；RoleAgentBench 支持离线知识与回应测量，不能据此证明开放社会持续演化。 |
| D07 | [CoSER: Coordinating LLM-Based Persona Simulation of Established Roles](https://proceedings.mlr.press/v267/wang25dk.html) | ICML 2025 | **M** | 从 771 本书提取人物场景、对白、动作与内心活动，训练共享角色模型并提出 GCA 复演评测；部分心理活动由教师推断，最多二十轮的文本复演不等于真实游戏执行，后续改变 judge 的分数不可直接拼榜。 |
| D08 | [Beyond Dialogue: A Profile-Dialogue Alignment Framework Towards General Role-Playing Language Model](https://aclanthology.org/2025.acl-long.586/) | ACL 2025 Main | **M** | 以角色、风格、情绪、关系和人格标签对齐 profile 与对白，再混合对齐任务训练；同规模数据对照支持设定一致性监督的价值，短场景与教师标签不能验证长期心理真实性。 |
| D09 | [OpenCharacter: Training Customizable Role-Playing LLMs with Large-Scale Synthetic Personas](https://arxiv.org/abs/2501.15427v2) | arXiv v2（2025-02-18）；未核实正式 venue | **M** | 从 PersonaHub 扩展约两万原创角色并合成角色化指令数据，提供区别于知名人物模仿的训练路线；PersonaGym 全集与 Light 子集结论不同，改善主要集中于部分维度，不能概称全面超过强闭源模型。 |
| D10 | [Codifying Character Logic in Role-Playing](https://papers.neurips.cc/paper_files/paper/2025/file/15294ba2dcfb4521274f7aa1c26f4dd4-Paper-Conference.pdf) | NeurIPS 2025 Main；核读正式版 | **M** | 将人物设定编译为带条件查询的可执行函数，拆分离线编译与在线生成；八十三角色场景预测支持结构化逻辑的效用，更新实验借助参考动作、Best@K 借助事后选择，不能等同自主演化与单次决策质量。 |
| D11 | [Deriving Character Logic from Storyline as Codified Decision Trees](https://aclanthology.org/2026.acl-long.568/) | ACL 2026 Main；CDT | **M** | 从场景—动作实例聚类、提出条件规则并以 NLI 验证，递归构造可解释决策树；测的是原作动作预测，语义条件仍由模型判断，静态离线树不构成心理机制或在线更新的形式化保证。 |
| D12 | [Identifying and Mitigating Bottlenecks in Role-Playing Agents: A Systematic Study of Disentangling Character Profile Axes](https://aclanthology.org/2026.emnlp-main.1590/) | EMNLP 2026 Main；FACD | **M** | 在信息量匹配的 211 个人设上拆分熟悉度、结构和道德倾向，提出字段级对比解码；结果受丰富设定、模型和任务条件约束，不能推断结构或熟悉度普遍无关，安全子测也不是对抗保证。 |
| D13 | [Neeko: Leveraging Dynamic LoRA for Efficient Multi-Character Role-Playing Agent](https://aclanthology.org/2024.emnlp-main.697/) | EMNLP 2024 Main | **M** | 用角色 profile 门控动态 LoRA 子块，并通过 fusion/expansion 支持角色共享及增量加入；九角色和 8+1 设置验证参数复用，未彻底消除角色串扰，也未验证千角色并发部署。 |
| D14 | [Impatient Users Confuse AI Agents: High-fidelity Simulations of Human Traits for Testing Agents](https://aclanthology.org/2026.acl-long.1743/) | ACL 2026 Main；TraitBasis / τ-Trait | **M** | 以对比样本激活差向量控制四类用户特征，评估客服工具智能体对非理想用户的鲁棒性；不是 SAE，有限特征组合不证明任意文学人格可连续独立控制，默认服务还依赖 STEER API。 |

## 4. 角色推理、偏好学习与多轮优化

| ID | 完整题名与原论文入口 | 年份、正式状态或核读版本 | 阅读 | 一句话贡献与证据范围 |
|---|---|---|---|---|
| R01 | [R-CHAR: A Metacognition-Driven Framework for Role-Playing in Large Language Models](https://aclanthology.org/2025.emnlp-main.1372/) | EMNLP 2025 Main | **M** | 利用教师评估、重采样与假设扩展构造角色思考数据，再 LoRA SFT 小模型；SocialBench 部分指标提高但风格、短记忆等有退化，“metacognition”首先指数据修订过程，不是已经验证的内在元认知。 |
| R02 | [Thinking in Character: Advancing Role-playing Agents with Role-Aware Reasoning](https://papers.nips.cc/paper_files/paper/2025/hash/aacca7b6a20d157112205a44f42821c8-Abstract-Conference.html) | NeurIPS 2025 Main；RAR | **M** | 结合人物情绪、经历、立场和动机的推理蒸馏，以及按场景匹配推理风格的偏好训练；消融支持角色化思考而非单纯增加 thinking tokens，文本推理风格不等于隐性人物状态的可验证机制。 |
| R03 | [CPO: Addressing Reward Ambiguity in Role-playing Dialogue via Comparative Policy Optimization](https://aclanthology.org/2025.findings-emnlp.18/) | EMNLP 2025 Findings | **M** | 用组内候选分析、排序和评分缓解开放式角色奖励的绝对分噪声；支持同底座上有限平均改善，RL 与 CharacterArena 的角色重叠、组内组成效应和主观 judge 仍限制泛化解释。 |
| R04 | [Act-Adaptive Margin: Dynamically Calibrating Reward Models for Subjective Ambiguity](https://aclanthology.org/2026.acl-long.710/) · [补充原始记录／版本](https://arxiv.org/abs/2505.23923) | ACL 2026 Main；AAM，前序题名 ChARM | **M** | 以动态 margin 和 SFT 正则校准主观偏好奖励，并在 Charm 数据和角色优化中验证；与旧版 ChARM 及相关数据名称按同一论文发展链计数，收益不代表奖励评审已经客观无偏。 |
| R05 | [HER: Human-like Reasoning and Reinforcement Learning for LLM Role-playing](https://aclanthology.org/2026.findings-acl.1283/) | ACL 2026 Findings | **M** | 分离系统思考与第一人称角色思考，结合按样例生成原则的奖励模型进行 RL；SFT、双层思考和 RL 贡献需分开，其 CoSER judge 与思想可见性已改变，不能与原版 CoSER 分数直接比较或视为硬 RLVR。 |
| R06 | [Character-R1: Enhancing Role-Aware Reasoning in Role-Playing Agents via RLVR](https://arxiv.org/abs/2601.04611v1) | arXiv v1（2026-01-08）；未核实正式录用记录 | **M** | 用认知焦点标签、属性与参考重叠奖励及角色条件归一化训练角色推理；650 样本上的代理指标改善不表示完整开放式表演具有唯一真值，也不能由异底座对照证明消除了 SFT 机械感。 |
| R07 | [VeriRole: Verifiable Role-Awareness through Hint-Guided Reinforcement Learning](https://proceedings.iclr.cc/paper_files/paper/2026/hash/12df08e9280061b4877f97598c644c3e-Abstract-Conference.html) · [补充原始记录／版本](https://arxiv.org/abs/2505.10218) | ICLR 2026；RAIDEN-R1 前序版本并入本条 | **M** | 生成来自 profile/历史的 hint，再以格式、来源、语义及答案反馈优化角色推理；含 embedding 和模型判分，非全部 rule-only，前序 RAIDEN-R1 的知识增益伴边界退化体现平均分掩盖的权衡。 |
| R08 | [CRPO: Character-centric Group Relative Policy Optimization for Role-aware Reasoning in Role-playing Agents](https://proceedings.mlr.press/v306/tang26c.html) | ICML 2026 | **M** | 分别处理任务组内优势和角色级风格优势，结合熵调节与通用回答负 anchor；同规模算法对照支持特定代理奖励下的改善，不能外推为普遍角色目标分解或与异规模 HER 直接比较。 |
| R09 | [MOA: Multi-Objective Alignment for Role-Playing Agents](https://aclanthology.org/2026.acl-long.531/) | ACL 2026 Main | **M** | 通过动态目标权重、pivot 与冲突样本筛选对齐对话、角色知识和风格，并加入思考和 off-policy 指导；需要分离各组件贡献，学习型 judge 与局部理论假设不支持全局 Pareto 最优保证。 |
| R10 | [Consistently Simulating Human Personas with Multi-Turn Reinforcement Learning](https://papers.nips.cc/paper_files/paper/2025/hash/4c91443877f8388d8190c938ac5a4d4d-Abstract-Conference.html) | NeurIPS 2025 Main | **M** | 对学生、来访者和聊天用户模拟进行多轮 PPO，以 profile-to-line、line-to-line 和问答探测评价一致性；静态身份保持的收益不等于真实人群行为效度，也可能惩罚合理信念与情绪变化。 |
| R11 | [Agentic Reinforcement Learning with Implicit Step Rewards](https://openreview.net/forum?id=ooROvpmxMV) · [补充原始记录／版本](https://arxiv.org/abs/2509.19199v3) | ICLR 2026；iStar；核读 arXiv v3 | **M** | 从轨迹偏好学习隐式过程奖励，再组合步骤与整段优势；角色相关证据来自 SOTOPIA 社交目标，WebShop 或推箱子的客观成功不能用来证明社会奖励或人物忠实度可验证。 |
| R12 | [Long-Short Horizon Reinforcement Learning for Persona-Level Role-Playing Agents](https://aclanthology.org/2026.findings-emnlp.1619/) | EMNLP 2026 Findings；LSH-RL | **M** | 以局部质量门控角色轨迹奖励，结合 DPO warm-start、对话 RL 和动作细化；PersonaArena/CharacterBox 支持文本互动的长短期目标协调，不证明 3D 引擎动作执行或普遍胜过 episode-only RL。 |
| R13 | [OSPD: On-Policy Self-Distillation for Persona-Consistent Dialogue](https://aclanthology.org/2026.emnlp-main.2105/) | EMNLP 2026 Main | **M** | 让完整人设 EMA 教师在学生短人设生成轨迹上蒸馏，并按熵选择 KL 方向、逐步遮蔽属性；证据针对 brief-profile 部署，默认 verifier 仍依赖外部模型，公开参考实现不含论文完整数据、评测包和权重。 |
| R14 | [KuaiRP Series Role-playing Models Technical Report](https://arxiv.org/abs/2609.11127v1) | arXiv v1（2026-09-10）；Kuaishou GameMind Lab 技术报告 | **M** | 报告特定小说世界的角色数据、格式/重复奖励及能力保持蒸馏，展示角色专门化与通用工具能力的权衡；局限于少量域内人物和内部评价，未核到完整开源模型、训练数据或代码。 |
| R15 | [MECoT: Markov Emotional Chain-of-Thought for Personality-Consistent Role-Playing](https://aclanthology.org/2025.findings-acl.435/) | ACL 2025 Findings | **M** | 将二维情绪环上的离散状态转移与人格、上下文推理结合，提供 RAPD 与情绪一致性度量；情绪分类与模型评分不等于心理机制效度，ETCC 对相关系数平方会丢失方向信息。 |

## 5. 知识边界、记忆使用与角色状态演化

| ID | 完整题名与原论文入口 | 年份、正式状态或核读版本 | 阅读 | 一句话贡献与证据范围 |
|---|---|---|---|---|
| M01 | [TimeChara: Evaluating Point-in-Time Character Hallucination of Role-Playing Large Language Models](https://aclanthology.org/2024.findings-acl.197/) | ACL 2024 Findings | **M** | 以未来、在场/不在场和过去事实/错误前提测试点时间幻觉，并用 temporal/spatial experts 与 cutoff-RAG 改善边界；不在场主要检查是否谎称亲历，尚非完整信息传播与错误信念追踪。 |
| M02 | [Towards Lifelong Dialogue Agents via Timeline-based Memory Management](https://aclanthology.org/2025.naacl-long.435/) | NAACL 2025 Main；THEANINE | **M** | 把事件记忆组织为时间线和关系，在回答时检索并细化相关演变链；三至五会话和 TeaFarm 支持保留变化过程，但不代表所有历史无损，也不直接验证虚构人物长期关系演化。 |
| M03 | [BOOKMARKS: Checkpoint-Accelerated Active Grounding for Role-Playing](https://arxiv.org/abs/2605.14169v2) | arXiv v2（2026-09-26）；题名较初版已更新 | **M** | 按场景复用或创建 concept/state/behavior bookmark，仅同步其上次位置以来的叙事后缀；增量成本与原作动作预测得到测试，Best@3 仍含事后选优，不能等同分支游戏中的单次自主行动。 |
| M04 | [From Facts to Insights: A Persona-Driven Dual Memory Framework and Dataset for Role-Playing Agents](https://aclanthology.org/2026.findings-emnlp.270/) | EMNLP 2026 Findings；RoleMemo / DualMem | **M** | 分别写入事实与带证据链接的人格条件 insight，并用 RoleMemo 和 writer RL 检验主观解释记忆；逆向合成数据和共享 judge 限制外部效度，公开代码不等于完整数据与 RL agent 已发布。 |
| M05 | [ArcANE: Do Role-Playing Language Agents Stay in Character at the Right Time?](https://aclanthology.org/2026.emnlp-main.1998/) · [补充原始记录／版本](https://arxiv.org/abs/2606.05553v2) | EMNLP 2026 Main；核读 arXiv v2（2026-09-02） | **M** | 在同一人物不同叙事 phase 下询问相同场景，区分动作、理由与轨迹方向，并用相邻错误阶段作偏好负例；角色弧线忠实不等于在线双向关系成长，逐阶段奖励提升也不保证整体轨迹改善。 |
| M06 | [DREAM: LLM-based Dynamic Role-playing via Event-Aware Memory Graph](https://doi.org/10.1145/3770855.3818027) · [补充原始记录／版本](https://arxiv.org/abs/2608.05170) | KDD 2026 Main | **M** | 从已完成小说构建事件、时间和叙事因果图，在当前节点生成动态 profile；TCM 与角色评测支持离线时间定位，新增互动的在线图更新仍属未来工作，pairwise 胜率不是绝对边界准确率。 |
| M07 | [Staying In Character: Perspective-Bounded Memory For Book-Based Role-Playing Agents](https://arxiv.org/abs/2606.25632v1) | arXiv v1（2026-06-24）；REVERIEMEM / KBF-QA | **M** | 结合第一人称 episodic memory、带角色可见性的事实图及情绪表达模式，在 KBF-QA 同时测可知回答与拒知；可见性规则与 benchmark 定义相关，检索过滤不等于清除参数知识或解决多级传闻。 |
| M08 | [PersMem: Internalizing Personality into Dual-Pathway Memory for LLM Agents](https://arxiv.org/abs/2609.34372v1) | arXiv v1（2026-09-28） | **M** | 将预定义人格映射到情绪评价、保留与被动/主动检索参数，测量依恋和 Big Five 条件下的行为差异；手工校准、短对话及小规模配对限制心理外推，引用旧 CoSER 分数不是同 judge 的公平 SOTA 比较。 |
| M09 | [The Curse of Knowledge in Role-Playing Language Models](https://arxiv.org/abs/2610.17327v1) | arXiv v1（2026-10-12） | **M** | 用仅改变隐藏事实的反事实场景对照区分信息泄漏与猜测，比较自报可知性、语言及搜索行为；过滤到角色观察视图有效但依赖正确权限元数据，文本描述的听看测试不是实际感知实验，也非所有模型普遍失败。 |
| M10 | [REMP: A Structured Event-Probing Benchmark for Long-Horizon Role-Playing Dialogue](https://aclanthology.org/2026.findings-emnlp.602/) | EMNLP 2026 Findings | **M** | 以关系、情绪、记忆和人格四维事件锚点评价长历史后的诊断分支；约八百轮是预制背景长度，不是被测模型完整自由 rollout，当前公开样例也不能当作已释放全八十轨迹。 |
| M11 | [Memory-Driven Role-Playing: Evaluation and Enhancement of Persona Knowledge Utilization in LLMs](https://aclanthology.org/2026.findings-acl.1175/) | ACL 2026 Findings；MRBench / MRPrompt | **M** | 拆分 anchoring、selecting、bounding、enacting，比较同内容不同 persona schema 与推理提示；输入中的记忆不是直接测参数记忆，给定历史的下一回复也不等于外部记忆写入或长程状态维护。 |
| M12 | [StratMem-Bench: Evaluating Strategic Memory Use in Virtual Character Conversation Beyond Factual Recall](https://aclanthology.org/2026.acl-long.1491/) | ACL 2026 Main | **M** | 在固定记忆池内区分必要、可选和无关信息，测选择完整性与自然融入；judge 检测后规则聚合仍依赖语义评判，结果只支持 read/use 能力，不能推出存储、检索和遗忘质量。 |
| M13 | [SubtleMemory: A Benchmark for Fine-Grained Relational Memory Discrimination in Long-Horizon AI Agents](https://aclanthology.org/2026.findings-emnlp.1199/) | EMNLP 2026 Findings | **M** | 以互补、情境差异和矛盾事实检验顺序写入、检索及生成，并用 oracle 诊断瓶颈；这里 relational 指事实关系，固定历史 replay 的单次回答不衡量人际关系、人格或在线情绪演化。 |

## 6. 综合评测、人格测量、指令与安全

| ID | 完整题名与原论文入口 | 年份、正式状态或核读版本 | 阅读 | 一句话贡献与证据范围 |
|---|---|---|---|---|
| E01 | [InCharacter: Evaluating Personality Fidelity in Role-Playing Agents through Psychological Interviews](https://aclanthology.org/2024.acl-long.102/) | ACL 2024 Main | **M** | 将十四类量表改成开放访谈，以隔离上下文、匿名化和不同映射方式评估人物人格忠实度；金标准包含读者投票与解释，量表吻合不是临床人格或情境行为真实性。 |
| E02 | [CharacterEval: A Chinese Benchmark for Role-Playing Conversational Agent Evaluation](https://aclanthology.org/2024.acl-long.638/) | ACL 2024 Main；CharacterRM | **M** | 提供中文文学人物多维回复评测、人类标注与 CharacterRM；主要测固定历史下下一回复，按 example 划分可能共享原对话，奖励模型未被证明消除长度偏差或适用于所有人物价值观。 |
| E03 | [RoleMRC: A Fine-Grained Composite Benchmark for Role-Playing and Instruction-Following](https://aclanthology.org/2025.findings-acl.1082/) | ACL 2025 Findings | **M** | 组合角色专业边界、阅读理解、嵌套格式和多轮优先级规则，并分析 SFT/DPO 激活变化；专业相关性代理不是真实知识边界，局部神经元缩放实验不证明普遍的角色—指令机制分离。 |
| E04 | [Persistent Personas? Role-Playing, Instruction Following, and Safety in Extended Interactions](https://aclanthology.org/2026.eacl-long.246/) | EACL 2026 Main | **M** | 比较访谈与目标任务中百轮级历史下的人格淡化、指令遵循和安全变化；人设趋向无 persona 基线可伴随拒答增加，不能将这种副作用当作角色与安全同时改善。 |
| E05 | [Beware of Your Po! Measuring and Mitigating AI Safety Risks in Role-Play Fine-Tuning of LLMs](https://aclanthology.org/2025.acl-long.544/) | ACL 2025 Main；SaRFT | **M** | 测量角色 SFT 的安全退化，并对风险代理选中的样本加强相对安全底座的约束；拒答率及有限 RoleBench 指标支持折中改善，不能称安全底线被锁死或所有沉浸体验无损。 |
| E06 | [Knowing-but-Doing: Diagnosing and Defending Role-Play-Driven LLMs Jailbreaks via Moral Disengagement](https://aclanthology.org/2026.findings-acl.349/) | ACL 2026 Findings；MD-Trace / MD-Shield | **M** | 拆分任务、人物和情境压力，观察风险识别文本与危险遵从并存，再训练角色内安全回应；可见 reasoning 不是内部道德心理的直接证据，静态攻击效果不等于长期防护保证。 |
| E07 | [PersonaGym: Evaluating Persona Agents and LLMs](https://aclanthology.org/2025.findings-emnlp.368/) | EMNLP 2025 Findings | **M** | 对二百个人设在环境适应、人格一致等五类任务生成一万问题，并用 ensemble 与示例化 rubric 评价；动态生成题目不等于长期自由交互，模型规模与得分关系仅对该任务和 judge 成立。 |
| E08 | [RAIDEN Benchmark: Evaluating Role-playing Conversational Agents with Measurement-Driven Custom Dialogues](https://aclanthology.org/2025.coling-main.735/) | COLING 2025 Main | **M** | 由标注者针对十一维构建 135 角色多轮对话，采用固定历史续写和成对 RPCAJudger；不是全程自由互动，105 个训练角色资料与三十个公开测试角色的资源范围需区分。 |
| E09 | [DynSess: Dynamic Session-Level Evaluation and Optimization Framework for Role-Playing Agents](https://aclanthology.org/2026.findings-emnlp.689/) | EMNLP 2026 Findings | **M** | 以整段互动 rubric、前瞻轨迹搜索和 DSPO/GSRPO 优化会话质量；默认评价是在不同长度前缀后续写短段，学得 judge 奖励不是硬真值，自动分与人类偏好改善幅度也不相同。 |
| E10 | [FURINA: A Fully Customizable Role-Playing Benchmark via Scalable Multi-Agent Collaboration Pipeline](https://arxiv.org/abs/2510.06800v3) | arXiv，首发 2025；核读 v3（2026-04-06），未核实正式 venue | **M** | 通过多智能体构造可指定人物、情境与指标的评测数据，覆盖已知/原创及中英角色；实际评价为固定历史下一句，模型样本上的性能—幻觉权衡不是普遍 Pareto 定理或闭环多人社会证明。 |
| E11 | [DMT-RoleBench: A Dynamic Multi-Turn Dialogue Based Benchmark for Role-Playing Evaluation of Large Language Model and Agent](https://ojs.aaai.org/index.php/AAAI/article/view/34768) | AAAI 2025；39(24):25760–25768 | **M** | 以 996 个中文种子驱动闭环多轮访谈，用十四维 DMT-RM/DMT-Score 评价保持能力；多数维度采用前缀一错全错，曲线下降部分来自定义，官方仓库仍未核到种子与评测器的实际发布。 |
| E12 | [ToMATO: Verbalizing the Mental States of Role-Playing LLMs for Benchmarking Theory of Mind](https://ojs.aaai.org/index.php/AAAI/article/view/32143) | AAAI 2025；39(2):1520–1528 | **M** | 将角色合成的私有思想转为 5,401 道一/二阶心理状态问题，测试观察者从完整对话推断他人状态；标签不是实际心智真值，任务不直接评价 NPC 在线决策，作者建议数据仅用于评测，代码受 NTT 非商业研究评估许可约束。 |
| E13 | [RoleCDE: Benchmarking and Mitigating Role–Alignment Trade-offs in Role-Playing Agents](https://aclanthology.org/2026.findings-acl.106/) | ACL 2026 Findings；以正式 PDF 为准 | **M** | 用 7,957 个 profile–scenario 组合、23,871 个两选项 dilemma 测三种难度下角色与默认对齐的取舍；DBR 不是越高越好，人评边际分布接近不等于逐例一致，SFT/DPO 有通用指标损失；[作者仓库](https://github.com/rabbitrose/RoleCDE)已核 986 个 persona JSON 及训练／评价代码，公开子集不等于论文全池，未见权重、未执行复现。 |

## 7. 可执行世界、互动叙事与社会智能

| ID | 完整题名与原论文入口 | 年份、正式状态或核读版本 | 阅读 | 一句话贡献与证据范围 |
|---|---|---|---|---|
| G01 | [Learning to Speak and Act in a Fantasy Text Adventure Game](https://aclanthology.org/D19-1062/) | EMNLP-IJCNLP 2019；LIGHT | **M** | 提供有角色、地点、物品 affordance 与状态动作的人类对话环境，连接说话和执行；原评测主要是回复/动作排序预测，不能将其指标直接当现代开放 LLM 的长期任务或人物动机评分。 |
| G02 | [Generative Agents: Interactive Simulacra of Human Behavior](https://doi.org/10.1145/3586183.3606763) · [补充原始记录／版本](https://arxiv.org/abs/2304.03442) | UIST 2023 | **M** | 以记忆检索、反思和分层计划驱动二十五角色的小镇，展示日常行动和信息扩散；组件消融采访使用完整系统已有轨迹，不能据此量化移除组件对整段社会发展的因果效应。 |
| G03 | [IBSEN: Director-Actor Agent Collaboration for Controllable and Interactive Drama Script Generation](https://aclanthology.org/2024.acl-long.88/) | ACL 2024 Main | **M** | 导演根据剧情与玩家输入给演员发指示，演员维护角色目标、记忆和关系；有限戏剧中的剧情推进支持导演控制，目标完成与文本动作不等于自由玩家能动性或真实引擎状态。 |
| G04 | [HAMLET: A Hierarchical and Adaptive Multi-Agent Framework for Live Embodied Theatrics](https://iclr.cc/virtual/2026/poster/10009957) · [补充原始记录／版本](https://arxiv.org/abs/2507.15518v5) | ICLR 2026；核读 arXiv v5 | **M** | 分离离线剧目蓝图、在线规划/推进/叙述及快慢思考和沉默策略；道具动作由 narrator 判断，PAD 的 0.36 秒不等于全系统延迟，动作类未纳入部分量化评价且公开训练资产仍不完整。 |
| G05 | [AdaMARP: An Adaptive Multi-Agent Interaction Framework for General Immersive Role-Playing](https://aclanthology.org/2026.findings-acl.1563/) | ACL 2026 Findings | **M** | 用 Scene Manager 管理换场、说话者、角色加入和终止，配合 thought/action/environment/speech 交互数据；推进了动态场景与演员组织，但文本环境及二十轮评价不代表真实物理世界或长期 campaign。 |
| G06 | [SocialBench: Sociality Evaluation of Role-Playing Conversational Agents](https://aclanthology.org/2024.findings-acl.125/) | ACL 2024 Findings | **M** | 区分个体角色能力与群体情境中的社会偏好，测试知识、风格、情绪和记忆；大量任务是静态群体上下文选择题或召回题，不能据此宣布 NPC 在线长期互动必然人格同化。 |
| G07 | [SOTOPIA: Interactive Evaluation for Social Intelligence in Language Agents](https://proceedings.iclr.cc/paper_files/paper/2024/hash/b3075b88e583a0e98d8b24338a613060-Abstract-Conference.html) · [补充原始记录／版本](https://arxiv.org/abs/2310.11667) | ICLR 2024 | **M** | 以双人角色、私有目标和七维评价构建交互式社会情境；目标得分受伙伴与 judge 影响，动作大体以文本表示，社会目标成功不能代替文学角色忠实或物理执行。 |
| G08 | [SOTOPIA-π: Interactive Learning of Socially Intelligent Language Agents](https://aclanthology.org/2024.acl-long.698/) | ACL 2024 Main | **M** | 结合专家行为克隆和自生成轨迹筛选后 SFT 学习社会策略；self-reinforcement 不是在线 policy-gradient/RLVR，自动评分增益与人评差距提示优化 judge 的风险。 |
| G09 | [SOTOPIA-Ω: Dynamic Strategy Injection Learning and Social Instruction Following Evaluation for Social Agents](https://aclanthology.org/2025.acl-long.1203/) | ACL 2025 Main | **M** | 在教师数据生成中动态注入谈判策略和阶段目标，再训练学生，增加复读与目标相关性评价；慢思考主要在数据阶段，不能推断学生在线成本或用自动目标分替代真人社交质量。 |
| G10 | [LIFELONG-SOTOPIA: Evaluating Social Intelligence of Language Agents over Lifelong Social Interactions](https://arxiv.org/abs/2506.12666v1) | arXiv v1（2025-06-14）；未核实正式 venue | **M** | 用固定角色对跨四十个 episode 的历史研究长期社会目标与关系条件化；随机目标未必需要历史，少量人工依赖任务才更直接暴露记忆不足，专属数据与代码未确认完整公开。 |
| G11 | [SOTOPIA-TOM: Evaluating Privacy and Information Management in Multi-Agent Interaction with Theory of Mind](https://arxiv.org/abs/2605.02307v2) · [补充原始记录／版本](https://proceedings.colm.cc/paper_files/paper/2026) | COLM 2026；核读 arXiv v2（2026-09-08） | **M** | 以公开/私聊可见性、分享政策和多方任务测信息路由，并比较 ToM 提示与显式信念状态；证据侧重职业协调中的隐私—效用权衡，不等于小说人物误信念或完整社会心理模拟。 |
| G12 | [Project Sid: Many-agent simulations toward AI civilization](https://arxiv.org/abs/2411.00114v1) | arXiv v1（2024-10-31）技术报告；未核实正式 venue | **M** | 用 PIANO 并发认知模块和 Minecraft 动作接口研究大规模协调、传播与制度内行为；法律/税制等有预设、超千 agent 运行会失稳，报告与展示仓库不等于已公开运行器或从零制度发明。 |
| G13 | [Setting the DC: Tool-Grounded D&D Simulations to Test LLM Agents](https://openreview.net/pdf?id=3Op7kJOvaD) · [补充原始记录／版本](https://genprocc.github.io/) | NeurIPS 2025 GenProCC Workshop；非主会 | **B** | 官方摘要提出以规则与工具驱动的 D&D 战斗评价工具使用、参数、表演、战术、状态和效率；PDF 访问受阻，仅核正式工作坊与摘要，不能借 2026 年新闻替代全文效果证据。 |
| G14 | [CriticaLLM: Using LLMs as Autonomous Game Master for Tabletop Role-Playing Games](https://arxiv.org/abs/2610.21525v1) | arXiv v1（2026-10-15） | **M** | 将简化桌游规则、地图、骰子和局部记忆接入自主 GM，测试叙事与对抗请求；三房间冒险和九名资深玩家的证据有限，选择影响感偏弱，不能说明通用长篇 GM 已成熟。 |

## 8. 视觉、视频与语音角色表演

| ID | 完整题名与原论文入口 | 年份、正式状态或核读版本 | 阅读 | 一句话贡献与证据范围 |
|---|---|---|---|---|
| V01 | [MMRole: A Comprehensive Framework for Developing and Evaluating Multimodal Role-Playing Agents](https://proceedings.iclr.cc/paper_files/paper/2025/hash/a5c7206fd66e8314bb21a04492359353-Abstract-Conference.html) · [补充原始记录／版本](https://arxiv.org/abs/2408.04203) | ICLR 2025 | **M** | 提供角色—图像—对话数据、模型和多维奖励评审，考察视觉理解与角色反应的一致；主要是静态图片和给定历史目标回复，不能等同连续视觉感知、角色实际视野或具身行动。 |
| V02 | [Video2Roleplay: A Multimodal Dataset and Framework for Video-Guided Role-playing Agents](https://aclanthology.org/2025.emnlp-main.1209/) | EMNLP 2025 Main | **M** | 从中文社交媒体视频构造角色对话并训练视频条件模型，探索时间信息和关键帧的价值；离线视频指标与单例多帧耗时不是实时流式互动证据，当前仓库仍有 Coming soon 资源缺口。 |
| V03 | [Through the Lens of Character: Resolving Modality-Role Interference in Multimodal Role-Playing Agent](https://arxiv.org/abs/2605.09443v1) | arXiv v1（2026-05-10）；CAVI | **M** | 通过视觉 anchor、低秩投影与角色条件干预缓解视觉—人设竞争；MMRole 上的小规模模型结果和理论假设支持早期探索，不证明普遍可控角色感知，training-free 也不等于无推理成本。 |
| V04 | [OmniCharacter: Towards Immersive Role-Playing Agents with Seamless Speech-Language Personality Interaction](https://aclanthology.org/2025.acl-long.1276/) | ACL 2025 Main | **M** | 连接语音理解、角色语言生成和语音输出，提供二十角色语音对话资源与模型；合成语音和同角色测试限制泛化，声线相似与报告的 speech latency 不能代替人格效度和全双工端到端体验。 |
| V05 | [OmniCharacter++: Towards Comprehensive Benchmark for Realistic Role-Playing Agents](https://ieeexplore.ieee.org/abstract/document/11506238) · [补充原始记录／版本](https://zchoi.github.io/OmniCharacter-plus/) | IEEE TPAMI 2026；只核元数据与资源 | **B** | 作者扩展到更广角色与场景并公布大型数据和 9B 权重；已核真实 HF 文件，未完成新版主文阅读，不能引用新版详细消融，数据卡与仓库许可描述也需分别核对。 |
| V06 | [ActorMind: Emulating Human Actor Reasoning for Speech Role-Playing](https://aclanthology.org/2026.findings-acl.1718/) | ACL 2026 Findings | **M** | 以 Eye/Ear/Brain/Mouth 组织情境情绪推断、同角色语音检索和 TTS；目标台词预先给定，RP-MOS 对错声线直接判最低分，小规模主观评价支持语音表演而非自由对话或行动智能。 |

## 9. 工业系统与实时部署：单独标注的工程来源

以下三篇均为官方工程来源，已阅读相关正文。它们补充语音链路、游戏引擎接口、推理调度和作者主张的运行约束；不与论文 benchmark 混成排行榜，也不将产品演示当作角色真实性的独立验证。

| ID | 官方文章与日期 | 本次采用的工程信息 | 证据边界 |
|---|---|---|---|
| B01 | [Ubisoft Reveals Teammates, an AI Experiment to Change the Game](https://news.ubisoft.com/it-it/article/3mWlITIuWuu0MoVuR6o8ps/ubisoft-reveals-teammates-an-ai-experiment-to-change-the-game)，2025-11-21 | 语音命令、同伴动作、作者设定的动机与世界观，以及封闭试玩中的 NPC 交互设计。 | 研究演示与有限试玩不证明长期剧情、所有玩家输入或正式产品可靠性。 |
| B02 | [Build On-Device AI Companions with the NVIDIA ACE Game Agent SDK and Unreal Engine 5 Plugins](https://developer.nvidia.com/blog/build-on-device-ai-companions-with-the-nvidia-ace-game-agent-sdk-and-unreal-engine-5-plugins/)，2026-06-16 | 本地 ASR／小语言模型／TTS、C++／Blueprint 游戏引擎集成，以及推理与图形计算共用设备的约束。 | SDK 能力与集成方式不是人格忠实度、社会智能或跨硬件性能的学术验证。 |
| B03 | [Inworld Inference 官方发布文章](https://inworld.ai/blog/introducing-inworld-inference)，2026-10-14 | 区分首 token 与 token 间延迟，讨论长输入短输出、缓存、调度及模型特定推理优化。 | 厂商报告的组件延迟不能直接替代含端点检测、网络、音频生成和打断恢复的端到端语音时延。 |

## 10. 版本与身份核查说明

- **RoleLLM** 的正式记录为 **ACL 2024 Findings**；**CharacterEval** 为 **ACL 2024 Main**，不是 EMNLP 2024。
- **More Than a Role** 是 **KDD 2026 PILA Workshop Oral**，该 workshop 为 **non-archival**；不能写成 KDD 主会 Oral。
- **Setting the DC / D&D Agents** 按 **NeurIPS 2025 GenProCC Workshop** 登记；2026 年新闻不是新的发表年份，另一个撤稿/withdrawn 的会议投稿版本不计正式录用。
- **FURINA、Character-R1、BOOKMARKS、CAVI、PersMem、REVERIEMEM、LIFELONG-SOTOPIA、OpenCharacter、Project Sid、CriticaLLM 和 KuaiRP** 按本次可核实的预印本或技术报告状态登记；不将尚未核实的 venue 传闻写入索引。
- **AAM／ChARM** 是同一论文的改名发展，合并为 R04；**VeriRole／RAIDEN-R1** 按同一研究发展链合并为 R07。**RAIDEN Benchmark** 是独立的 COLING 2025 评测论文 E08，不与 RAIDEN-R1 混淆。
- **RoleMRC、Role Consistency、RoleAgent** 即使被多个主题使用，也各只登记一次；BOOKMARKS、ArcANE、FURINA 等新旧 arXiv 版本不重复计数。
- **OmniCharacter++** 在本次仅核元数据和资源，未完成新版主文阅读；**Setting the DC** 因原文访问受阻也仅列 B。**Current Status, Challenges, and Future Trends** 保留为 T，不用其他综述的阅读量补足其阅读状态。
- **“有仓库”“有数据卡”“论文称公开”与实际可取得完整数据、代码、权重是不同状态。** 本索引只用资源核查限制论文可复用性的表述，没有将未运行的项目写成已复现。

阅读深度、发表身份和评价适用范围共同决定一条证据能支持什么结论。这里保留原文中的任务条件、代理指标和资源缺口，避免把角色对话、心理量表、社会目标、叙事推进与游戏执行误当作同一能力。



## 11. 增补：玩家—NPC 交互、人物状态与游戏接口（2026-10-30）

本轮新增 **8 篇独立论文**（M 2、T 4、B 2），与原 82 篇不重复计数。研究对象以 **Role-Playing 角色的状态、信念、言行和玩家侧输入**为中心。通用 Minecraft 任务分工、纯战斗 AI 和并发调度未因“Game Agent”名称而进入核心文献数量；Sony CPDC 是挑战资源、KRAFTON PUBG Ally 是工业工程资料，均不增加论文计数。

| ID | 完整题名与来源 | 年份／身份 | 阅读 | 方法与证据范围 |
| --- | --- | --- | --- | --- |
| A01 | [Codified Finite-State Machines for Role-playing](https://proceedings.iclr.cc/paper_files/paper/2026/hash/a862f5788fd09bb6843c694d8120d50c-Abstract-Conference.html) · [全文 HTML](https://arxiv.org/html/2602.05905v1) | ICLR 2026 | **M** | 从 profile 抽取关键心理/叙事状态及事件条件，用 LLM 编译可执行状态转移；CPFSM 加入状态概率。已知简化 FSM 的确定执行测试、Fandom 参考动作 NLI 与 Best@K 分别衡量不同方面；不是引擎动作验收或人物真实心理真值。直接连接 2025 Codified Profile 与 2026 CDT，但研究对象是**状态转移**，不能省略。 |
| A02 | [RMTBench: Benchmarking LLMs Through Multi-Turn User-Centric Role-Playing](https://aclanthology.org/2025.findings-emnlp.730/) | EMNLP 2025 Findings | **M** | 从玩家/用户目的而非原作人物知识出发，80 个角色、8,156 条中英话语；覆盖人物探查、人设坚持、隐含意图、偏好和敏感试探。用户发言固定，角色从首轮起自行生成前轮回复，介于静态续写与完全双向闭环之间；judge 依赖模型且部分维度校准有限。 |
| A03 | [PsyMem: Fine-grained Psychological Alignment and Explicit Memory Control for Advanced Role-Playing LLMs](https://aclanthology.org/2026.tacl-1.24/) | TACL 2026 | **T** | 用 26 个心理指标和显式 memory-alignment 训练角色行为，论文包含 5,414 个角色和 38,962 段小说对话。它不是仅用 RAG 召回、也不等于长周期玩家关系学习；本次仅定点核读，资源发布未完整审计。 |
| A04 | [Can LLM Agents Stick to the Script? A Benchmark for Long-Horizon Consistency in Interactive Narratives](https://proceedings.mlr.press/v306/ma26ap.html) | ICML 2026 | **T** | NCP-Bench 将 100 个叙事环境的初始事实、承诺和轨迹与模拟玩家干扰连起来；作者公开数据、评测 runner 和基线。被测对象是 narrator 而非受部分观察限制的单个 NPC；事实/承诺冲突部分由模型审计，不是引擎硬状态奖励。 |
| A05 | [MCPDial: A Minecraft Persona-driven Dialogue Dataset](https://arxiv.org/abs/2410.21627) | arXiv 首发 2024，正式 venue 未核实 | **T** | 将玩家—NPC 双侧 persona、长对话及话语之间的函数调用组合为合成监督数据，仓库已见训练/测试 JSON。函数调用标注没有引擎执行回执，不能称闭环行为成功。 |
| A06 | [Bayesian Social Deduction with Graph-Informed Language Models](https://aclanthology.org/2026.acl-long.1497/) | ACL 2026 Main | **T** | 以因子图跟踪 Avalon 隐藏身份，LLM 处理语言和发言，受控真人试验报告 67% 胜率。实验 agent **只扮演 Good 阵营**，所以不是反派欺骗型角色表演的直接证据。其对 RP 的意义是角色自己的信念、私有信息与策略性语言怎样分离。 |
| A07 | [Fake Player: Imitating Real Player to Distill Data for LLM-based NPC Training](https://openreview.net/pdf/2e26df077644bbbe3df13f485ea6433e09764b7b.pdf) | 匿名 ICLR 2026 投稿稿，未核正式录用 | **B** | 内心独白、意图栈和打字行为模拟玩家侧受限表达，并使用 Distill Bench 比较数据。明确提出玩家输入分布问题；模拟数据效果不等于已测真实玩家行为，完整发布与身份未核定。 |
| A08 | [Quest of Aivengarde: Comparative Study of Player Experience Across LLM Dialogue Systems](https://portal.findresearcher.sdu.dk/en/publications/quest-of-aivengarde-comparative-study-of-player-experience-across/) | FDG 2026 发表记录 | **B** | 对比 RPG 中静态、改写、混合和完全生成式 NPC 对话，64 位参与者的日志与问卷衡量开放性和体验。仅核正式摘要及元数据，未完整阅读实验，不能将“更长对话”自动解释为更忠实的人物。 |

**其他已核资料（不另计独立论文）**：[Sony CPDC 2025 官方 NPC 角色对话与函数调用任务](https://www.aicrowd.com/challenges/commonsense-persona-grounded-dialogue-challenge-2025/problems/task-oriented-dialogue-task-1)、[公开 starter kit](https://github.com/Augustus2011/sony-cpdc-2025-starter-kit)、[KRAFTON / NVIDIA 的 PUBG Ally 工程访谈（2026）](https://developer.nvidia.com/blog/how-krafton-built-pubg-ally-a-co-playable-character-powered-by-nvidia-ace/)。前者的动作函数无返回值，不能证明执行成功；后者展示世界状态查询和快慢执行分层，不是人物忠实度的独立学术 benchmark。

[The Price of Format（EMNLP 2025 Findings）](https://aclanthology.org/2025.findings-emnlp.836/) 对格式与输出多样性提供相邻机制证据，但它的核心测试是一般开放生成和故事续写，没有 NPC 角色化训练的直接对照；只在正文讨论可能的表达坍缩机制时引用，不进入本次新增的 8 篇核心文献计数。

## 12. 补充：Role-Play 自然性、迎合与动态人设评价

以下 3 篇直接研究人物扮演的质量，不扩大通用多 agent 协作的覆盖。与前面 90 篇去重。

| ID | 论文与来源 | 发表状态 | 阅读 | 方法和证据边界 |
| --- | --- | --- | --- | --- |
| P09 | [Deflanderization for Game Dialogue: Balancing Character Authenticity with Task Execution in LLM-based NPCs](https://arxiv.org/html/2510.13586) | 2025 arXiv 预印本、CPDC 参赛报告 | **M** | 简洁且不夸张的 fantasy RPG 角色提示，与 few-shot、CoT、函数提示和 Qwen3-14B LoRA 共同研究功能性回应与人物自然度。部分组合的比赛收益不证明 GRPO/DPO 普遍导致脸谱化或真实人格被形式化。 |
| P10 | [Too Nice to Tell the Truth: Quantifying Agreeableness-Driven Sycophancy in Role-Playing Language Models](https://aclanthology.org/2026.acl-long.1421/) | ACL 2026 Main | **T** | 275 合成人设、4,950 观点题、13 模型；9 个模型内宜人性与附和正相关，然而多数模型采用 persona 后较无 persona 的整体平均迎合下降。立场分类分数不是人物心理或真假事实的完备真值。 |
| P11 | [PersonaArena: Dynamic Simulation for Evaluating and Enhancing Persona-Level Role-Playing in Large Language Models](https://aclanthology.org/2026.findings-acl.471/) | ACL 2026 Findings | **T** | 从社会材料生成 persona bank 和多轮情境，使用多评审提供角色反馈；多 agent 在这里是评审方法，不是 NPC 合作研究，模拟角色与真人玩家的效度需分别理解。 |



## 13. Role-Play 核心研究补缺：心智、控制、奖励与人物评价（2026-10-30）

本轮根据新增聊天记录提供的线索逐项检索正式记录、原论文与作者公开资源，**只补与人物扮演直接相关的 20 篇独立论文**。它们与前 93 篇去重。这里的 T 表示有针对性地阅读主文方法、实验或讨论，但没有声称逐页精读完整论文；B 仅表示确认摘要、发表状态或作者资源。这 20 篇均为 2025–2026 年正式发表或首次公开的研究。

| ID | 论文与原始来源 | 正式状态 | 阅读 | 核心思想、真实证据与限制 |
| --- | --- | --- | --- | --- |
| N01 | [CharacterBench: Benchmarking Character Customization of Large Language Models](https://ojs.aaai.org/index.php/AAAI/article/view/34806) | AAAI 2025 | **T** | 3,956 角色/22,859 问题，六组 11 维综合人物评测；CharacterJudge 等配套工具。角色模型的共同参照，不等于全部维度都由独立客观真值评分。 |
| N02 | [Reasoning Does Not Necessarily Improve Role-Playing Ability](https://aclanthology.org/2025.findings-acl.537/) | ACL 2025 Findings | **T** | 比较直接、CoT 与推理模型在角色任务上的行为；常规长推理可能偏离角色视角，但不是所有思考都降低角色能力的通则。 |
| N03 | [Guess What I am Thinking: A Benchmark for Inner Thought Reasoning of Role-Playing Language Agents](https://aclanthology.org/2025.findings-emnlp.819/) | EMNLP 2025 Findings；RoleThink/MIRROR | **T** | 从 76 本书构建 6,058 条角色心理/内心活动条目，区分原文 Gold 与解释性 Silver，MIRROR 组织记忆与反思；部分测试子集不能冒充全库规模。 |
| N04 | [CharacterBox: Evaluating the Role-Playing Capabilities of LLMs in Text-Based Virtual Worlds](https://aclanthology.org/2025.naacl-long.323/) | NAACL 2025 Main | **T** | 角色 agent 在 narrator 驱动世界中选择行为与对白，另以 CharacterNR/CharacterRM 评价轨迹；LLM narrator 与可验证真实引擎要区分。 |
| N05 | [EmoCharacter: Evaluating the Emotional Fidelity of Role-Playing Agents in Dialogues](https://aclanthology.org/2025.naacl-long.316/) | NAACL 2025 Main | **T** | 将情绪触发与人物性格、单/多轮转移分开评价，六类指标揭示部分角色强化方式损害情绪忠实；不是心理生理学的客观情感读数。 |
| N06 | [R4: Nested Reasoning-Retrieval for Reward Modeling in Role-Playing Agents](https://openreview.net/pdf?id=sWQSbVsPEz) | ICLR 2026 | **B** | 重视 reward evaluator 自身的角色知识检索与分层推理；本次只核正式状态、方法摘要和来源，完整代码/消融尚未核实。 |
| N07 | [RoleRMBench & RoleRM: Towards Reward Modeling for Profile-Based Role Play in Dialogue Systems](https://arxiv.org/abs/2512.10575) | arXiv 2025 预印本 | **T** | 七类角色偏好子任务与 CIP/候选排序奖励，评估泛用 RM 失配；本论文设置中最高分不代表开放式人物真值，完整更新权重尚待发布。 |
| N08 | [PERSONA: Dynamic and Compositional Inference-Time Personality Control via Activation Vector Algebra](https://proceedings.iclr.cc/paper_files/paper/2026/hash/f66ce276436c4cd151535b03841ac713-Abstract-Conference.html) | ICLR 2026 | **T** | 对比激活特质向量、动态缩放/组合和 Persona-Evolve；可组合的行为效果不证明人格维度严格独立。 |
| N09 | [Enhancing Persona Following at Decoding Time via Dynamic Importance Estimation](https://arxiv.org/abs/2603.01438) | ICLR 2026，PDD | **T** | 根据当前上下文估计人设属性相对重要性，并在 token 解码时对比分布；优化目标的等号条件不是人物心理真实度定理。 |
| N10 | [Facet-Level Persona Control by Trait-Activated Routing with Contrastive SAE for Role-Playing LLMs](https://arxiv.org/abs/2602.19157) | arXiv 2026 预印本 | **T** | Big Five facet 对比数据、SAE 潜变量和情境路由；它与普通残差激活方向不是同一方法，公开完整训练/权重未核定。 |
| N11 | [Know Thyself, Know Thy User: Intrinsic Dual-Perspective Reasoning for Role-Playing LLMs](https://proceedings.mlr.press/v306/sun26at.html) | ICML 2026；KSKT | **T** | Transformer self-role 与 other-user 两路条件融合，直接刻画人物立场与玩家需求之间的张力；示例代码不意味着完整训练权重已发布。 |
| N12 | [When Roleplaying, Do Models Believe What They Say?](https://arxiv.org/abs/2606.11502) | arXiv 2026 预印本 | **T** | 角色假信念、质询与线性 truth probe 的表征/行为关联；probe 不会直接读出模型真实“心理信念”。 |
| N13 | [Beyond Static Persona Consistency: Dynamic Persona Coherence in LLM Role-Playing](https://aclanthology.org/2026.acl-long.1336/) | ACL 2026 Main | **T** | 长/中/短时间尺度的稳定身份与动态情绪、PCC/PCR/PDS 校正；少量角色与自设 judge 的增益不能外推为普适心理机制。 |
| N14 | [PersonaForge: Psychology-Grounded Dual-Process Architecture for Personality-Consistent Role-Playing Agents](https://aclanthology.org/2026.findings-acl.386/) | ACL 2026 Findings | **T** | 多层心理状态和选择性 inner monologue，关注 50 轮人格保持与开销；公开代码不附有版权人物原文数据。 |
| N15 | [If an LLM Were a Character, Would It Know Its Own Story? Evaluating Lifelong Learning in LLMs](https://aclanthology.org/2026.acl-long.1659/) | ACL 2026 Main；LifeState-BENCH | **T** | Hamlet 与合成分幕剧情的经历、自我与关系状态追踪；静态历史或有序事件 probe 不等于真实玩家生命周期的在线参数学习。 |
| N16 | [Rethinking Role-Playing Evaluation: Anonymous Benchmarking and a Systematic Study of Personality Effects](https://aclanthology.org/2026.sigdial-1.15/) | SIGDIAL 2026 | **T** | 匿名人物名字，保留描述并测试预训练知名度依赖；匿名化同时会删除合法语境线索，下降并不一概是作弊。 |
| N17 | [Too Good to be Bad: On the Failure of LLMs to Role-Play Villains](https://aclanthology.org/2026.findings-acl.282/) | ACL 2026 Findings | **T** | Moral RolePlay 的价值倾向人物测试，揭示部分模型易同化为亲社会助手；无法凭均分将原因全部归给 safety alignment。 |
| N18 | [Beyond Borrowed Histories: Person-Aligned User Simulation for Interactive Role-Playing Evaluation](https://arxiv.org/abs/2607.27816) | arXiv 2026 预印本；PALATE | **T** | 116 真人会话、5 个用户模拟 LoRA、约 1,600 条轨迹，研究用户模拟和 persona 评价的对齐；模型用户仍不同于真人。 |
| N19 | [CHARM: Character Hallucination for Multicultural Role Play Benchmark](https://aclanthology.org/2026.findings-emnlp.460/) | EMNLP 2026 Findings | **B** | 多语言/文化与角色知识幻觉维度；本次仅核原始元数据、摘要及任务范围，不推断未核读的方法细节和资源完备性。 |
| N20 | [MERRY: Semantically Decoupled Evaluation of Multimodal Emotional and Role Consistencies of Role-Playing Agents](https://arxiv.org/abs/2602.21941) | arXiv 2026 预印本 | **B** | 关注多模态角色感知、情绪与人设的解耦评价；只核摘要与资源声明，不将其列为已核完整评测包。 |

**与旧条目的区分**：PERSONA 的残差向量加减、CV-SAE 的稀疏潜特征路由、PDD 的 token 分布控制、KSKT 的 attention 结构改造不是同一种“人格 steering”；LifeState 的事件问答、ArcANE 的角色弧线和 RoleMemo 的主观洞察不是同一种“长期记忆”；RoleRMBench 的评审准确率与 HER-RM 在政策优化后的效果不是同一分数表。Gemini 关于顶会可投性、无需复杂工程就能完全复现、以及特质已被证明严格正交的表述不据此直接写入路线图。

