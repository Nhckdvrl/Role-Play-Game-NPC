# Role-playing 与 NPC Agent：数据、评测与实现资源地图

> 访问与核验日期：**2026-10-29 UTC**。本文是 [研究 Roadmap](../ROADMAP.md) 的资源配套文档，按资源实际承担的任务组织，不按模型榜单或选题优先级排列。收录经典基础资源及 2025–2026 年的主要延伸；同一论文的数据、代码和权重合并为一项，同一研究的前后版本不重复计数。

## 1. 如何阅读这张地图

论文给出的规模、当前能下载的规模和实际可运行的系统是三个不同对象。本表在能够核验时分别写明，尤其区分训练语料、独立测试集、历史回放、短分支续写和从头生成的交互轨迹。一个资源拥有几十万 token 的历史，并不表示被测 agent 自己完成了相同长度的闭环交互；小说中的时间顺序，也不等于真实玩家参与的关系演化。

发布状态采用以下含义，状态只覆盖本次确实检查的部分：

| 标记 | 本文所依据的证据 | 不包含的承诺 |
| --- | --- | --- |
| **实查** | 已查看仓库文件树、具体数据文件、数据集文件列表或模型权重分片；行内说明检查对象 | 不表示已下载全部大文件、执行训练、完成复现或验证论文分数 |
| **项目页** | 作者 README、项目主页或模型卡给出资源与使用说明，尚未核完对应资产 | 不把“计划发布”“链接存在”视为实现完成 |
| **论文自述** | 原论文声称存在或将公开某资源，本次只核到该声明 | 不表示当前公开可下载 |
| **待核** | 未确认具体文件，或访问受限、抓取失败、版本尚未对应 | 不表示资源不存在，也不推断作者未开展实验 |

**本次没有运行任何论文训练或复现实验。** “可比较基线”列记录原文采用或任务上直接对应的基线家族，不给出跨论文统一排名。只有角色划分、输入信息、底座、训练预算、生成长度、交互伙伴、评审模型和测试协议足够一致时，数值才具有直接可比性。完整正式题名与方法分析见 Roadmap；这里保留辨识度较高的论文名、正式记录和资源入口。

## 2. 角色训练语料：经历、对白、原创人设与人格倾向

这些资源首先提供监督数据。它们所包含的测试划分可以支持特定评测，但不能把训练部分直接当作独立 benchmark；“测试角色未参与微调”也不代表该角色的原作知识没有进入底座预训练。

| 资源与论文 | 任务、规模与测量边界 | 可比较基线家族 | 实际发布情况 |
| --- | --- | --- | --- |
| **A01 Character-LLM** · [EMNLP 2023 Main](https://aclanthology.org/2023.emnlp-main.814/) | 9 个角色，各约 1.4–2.2K 条重构经历，平均 13.2 轮；训练角色经历、回忆和保护性回复。是一人一模型的早期训练资源，经历不等于真实人物心理记录。 | 同底座 profile prompting、经历 SFT、保护性经历消融；与统一多角色模型比较时要计入每角色参数成本。 | [代码](https://github.com/choosewhatulike/trainable-agents)；[数据](https://huggingface.co/datasets/fnlp/character-llm-data)有实际文件。项目提供 9 个角色的 `wdiff` 权重入口，需原始 LLaMA 合并，不能当作独立完整模型直接加载。 |
| **A02 RoleLLM / RoleBench** · [ACL 2024 Findings](https://aclanthology.org/2024.findings-acl.878/) | 100 角色，95 英文、5 中文；168,093 样本、23,463 个独立指令。结合角色知识构造与角色化通用指令，区分指令泛化和角色泛化。 | profile 提示、检索增强、原对白 SFT、共享模型的条件化 SFT；需要匹配角色和指令 split。 | [代码](https://github.com/InteractiveNLP-Team/RoleLLM-public)；[RoleBench](https://huggingface.co/datasets/ZenMoore/RoleBench)已见实际 JSONL。论文模型 checkpoint 未完整确认，数据公开不等于论文权重齐全。 |
| **A03 DITTO / WikiRole** · [ACL 2024 Main](https://aclanthology.org/2024.acl-long.423/) | 3,902 训练角色、7,086 段对话、36,164 轮；另测 100 个未见角色。通过角色相关与对比问题生成自对齐数据，边界拒答属于输出行为约束。 | 相同底座的 profile 提示、普通 SFT、自蒸馏、外部教师蒸馏。论文使用去除原角色数据的修改版 Qwen 底座，与公开标准底座不宜直接混比。 | [作者项目](https://github.com/OFA-Sys/Ditto)已确认；本次没有完成所有数据、权重和生成流水线的文件级核验，标为**项目页**。 |
| **A04 CoSER / GCA** · [ICML 2025](https://proceedings.mlr.press/v267/wang25dk.html) | 771 本书、17,966 个角色、29,798 段对话，平均 13.2 轮；含情境、思想、动作、对白。GCA 测试含 200 个场景、最多 20 轮，区分见过作品的新剧情与新作品。思想标签含模型推断成分。 | 同底座 profile/RAG、对白 SFT、加入或移除 thought/action 的训练；GCA 的交互伙伴与思想可见性需保持一致。 | **实查**：[代码](https://github.com/Neph0s/CoSER)、[数据](https://huggingface.co/datasets/Neph0s/CoSER)、[8B](https://huggingface.co/Neph0s/CoSER-Llama-3.1-8B)与[70B](https://huggingface.co/Neph0s/CoSER-Llama-3.1-70B)模型资产。HER 等后续工作修改评审协议，不能直接拼接为同一榜单。 |
| **A05 Beyond Dialogue** · [ACL 2025 Main](https://aclanthology.org/2025.acl-long.586/) | 123 部小说/剧本、311 个角色（280 中文、31 英文）、3,552 场景、23,247 轮；用多种 profile–dialogue 对齐任务训练。新角色/新场景评测为 300 组、5 轮，不是长期闭环。 | 同 Qwen2-7B、等量数据的 SFT；不同对齐任务消融与 profile prompting。 | [代码](https://github.com/yuyouyu32/BeyondDialogue)可见数据构造与 AutoRPEval；[数据](https://huggingface.co/datasets/yuyouyu/BeyondDialogue)、[模型集合](https://huggingface.co/collections/yuyouyu/role-playing-bd-66d152b7daa6402d561b42fa)有公开入口。未执行完整训练和评测。 |
| **A06 OpenCharacter** · [arXiv 2025](https://arxiv.org/abs/2501.15427) | 约 20K 合成原创人设；从 LIMA、Alpaca、PH-Instruct 等问题产生角色化回答，同一问题分配多个角色。偏重可定制人设，不专门验证文学原作知识。 | 同 LLaMA-3-8B-Instruct 的原底座、改写数据、重新生成数据、SFT。PersonaGym 全集与 Light 子集分数不能混用。 | **实查**：[数据](https://huggingface.co/datasets/xywang1/OpenCharacter)包含 `synthetic_character.jsonl` 与 `synthetic_dialogue.jsonl`。作者训练权重与完整实现本次未确认。 |
| **A07 RolePersonality / Capturing Minds, Not Just Words** · [EMNLP 2024 Findings](https://aclanthology.org/2024.findings-emnlp.853/) | 46 个训练角色；继承 InCharacter 的 14 类量表访谈问题。Full+Single 32,089、Part+Single 22,489、Part+Multi 32,767 样本，Multi 为 5 轮。它是教师生成的人格指示训练集，不是独立人类心理访谈真值。 | 同 Mistral-7B、约 20K 样本预算的 RoleBench、Character-LLM、各人格语料子集；动机评估另用 CRoSS 445 道选择题。 | **实查**：[代码](https://github.com/alienet1109/RolePersonality)、[三个数据文件](https://huggingface.co/datasets/alienet/RolePersonality)。[Anthology 数据附件](https://aclanthology.org/2024.findings-emnlp.853.data.zip)有入口但未解包；LoRA/checkpoint 待核。训练与测试共享量表框架，应与角色划分一并说明。 |

## 3. 推理、偏好优化与交互训练：方法有代码，不一定有完整训练资产

### 3.1 角色化推理与奖励数据

| 资源与论文 | 任务、规模与测量边界 | 可比较基线家族 | 实际发布情况 |
| --- | --- | --- | --- |
| **B01 R-CHAR** · [EMNLP 2025 Main](https://aclanthology.org/2025.emnlp-main.1372/) | 使用来自 RoleBench、CRoSS、PersonaHub 的 1,426 个 profile，以 Qwen2.5-32B 教师搜索角色化推理，再训练 7B LoRA。中间推理文本不直接证明真实心智机制。 | 无推理 SFT、通用推理蒸馏、角色化搜索数据；同底座和 SocialBench 等固定测试。 | [仓库](https://github.com/lavapapa/R-CHAR)提供服务、基础调用与评价示例；完整训练数据、论文 checkpoint 本次未逐项确认，不能仅据示例称完整复现包。 |
| **B02 Thinking in Character / RAR** · [NeurIPS 2025 Main](https://papers.nips.cc/paper_files/paper/2025/hash/aacca7b6a20d157112205a44f42821c8-Abstract-Conference.html) | RoleBench 衍生数据上的角色化思想 SFT（RIA）和偏好优化（RSO）；LLaMA-3-8B。重点是角色条件下的推理结构，不是无限增加 thinking tokens。 | 无角色推理、通用蒸馏、MoreThink、RIA/RSO 消融；生成预算和教师强度影响解释。 | [代码](https://github.com/Toyhom/thinking_in_character)；**实查**[数据](https://huggingface.co/datasets/Toyhom/thinking_in_character_datas)有角色化与对比 JSON。论文训练权重待核。 |
| **B03 CPO / RoleplayPref / CharacterArena** · [EMNLP 2025 Findings](https://aclanthology.org/2025.findings-emnlp.18/) | RoleplayPref 含 1,108 角色、16,888 段对话；比较式 RM 对同组候选排序。CharacterArena 294 个 profile、15 轮；论文训练与评价使用相同的这组角色，不能标为未见角色泛化。 | pointwise RM、比较式 RM、相同策略底座的 GRPO；同组采样数、候选质量影响奖励学习。 | 本次未确认精确官方完整代码、CharacterArena 数据与权重下载；按**论文自述/待核**记录。与下项 Charm 有明显数据谱系联系，不能简单相加为两个独立规模。 |
| **B04 AAM / ChARM** · [ACL 2026 Main](https://aclanthology.org/2026.acl-long.710/) | Charm：1,108 角色、16,888 段对话、230 个虚拟用户；RoleReward 4,000、DialogueQuality 800。以自适应 margin 学习偏好奖励，另有 10 位标注者的模型偏好评价。 | Bradley–Terry RM、相同 7B/32B 底座 GRPO、固定/自适应 margin 消融。角色魅力与人物忠实不是同一指标。 | [仓库](https://github.com/calubkk/AAM)可见两个 Charm 数据目录，但 README 仍有 Code and data coming soon 声明；未核完目录内容、完整训练流程和权重，不能标全部已开源。ChARM 与 AAM 按同一研究演进处理。 |
| **B05 HER** · [ACL 2026 Findings](https://aclanthology.org/2026.findings-acl.1283/) | Qwen3-32B；系统思考与第一人称思想分离，RM 根据案例产生原则，原则池 51 项、12 维。CoSER 20 轮与 MiniMax 100 轮评价；其 CoSER 评审可见角色思想，协议不同于原 CoSER。 | 同底座 SFT、移除系统思考、不同 RL/奖励配置；比较时需对齐评审可见信息。 | **实查**：[代码](https://github.com/cydu24/HER)、[HER-Dataset](https://huggingface.co/datasets/ChengyuDu0123/HER-Dataset)、[HER-32B](https://huggingface.co/ChengyuDu0123/HER-32B)、[HER-RM-32B](https://huggingface.co/ChengyuDu0123/HER-RM-32B)实际 JSONL 与权重分片。存在权重不代表已验证 100 轮结果。 |
| **B06 Character-R1** · [arXiv 2026](https://arxiv.org/abs/2601.04611) | 使用 CharacterBench 的 650 条训练样例、10 个认知焦点标签与角色条件归一化。标签、格式和参考重叠提供代理奖励，不是完整人格的客观判定器。 | 同底座 SFT、GRPO、认知焦点/角色归一化消融；原测试数据必须与训练 650 条区分。 | **实查**[仓库](https://github.com/Toyhom/Character-R1)有 EasyR1 目录，但 README 为空；训练数据、论文权重与完整评价入口未确认。正式会议状态本次未核实，保留 arXiv。 |
| **B07 VeriRole** · [ICLR 2026](https://proceedings.iclr.cc/paper_files/paper/2026/hash/12df08e9280061b4877f97598c644c3e-Abstract-Conference.html) | 训练资源含 2,197 知识/记忆、567 边界/主题、500 闲聊样例，以及 737 对话、328 谜题相关材料；RAIDEN 独立测试 483 例。提示追踪、格式和语义评分的可验证程度不同。 | SFT、GRPO、去除 hint 或回答奖励；相同知识条件与测试角色。RAIDEN-R1 是前序版本，不另算一项。 | **实查**[仓库](https://github.com/FrontierLabs/VeriRole)当前仅 README 与 `VeriRole_train_v1.json`；训练 JSON 已发布，不等于完整训练代码、评测脚本或 checkpoint 已发布。 |

### 3.2 多目标、跨角色与闭环轨迹训练

| 资源与论文 | 任务、规模与测量边界 | 可比较基线家族 | 实际发布情况 |
| --- | --- | --- | --- |
| **B08 CRPO** · [ICML 2026](https://proceedings.mlr.press/v306/tang26c.html) | Qwen3-8B、650 条 CharacterBench 训练样例；角色级风格 advantage 与问题级任务 advantage 分开归一化。资源复用不代表新建独立大规模角色训练集。 | 同底座、同数据的 PPO、GRPO、DAPO、GSPO、GDPO、OAR；奖励和推理预算需对齐。 | **实查**[代码](https://github.com/Toyhom/CRPO)有 EasyR1、启动脚本与配置，示例涉及 8 GPU；完整数据包与训练 checkpoint 待核。 |
| **B09 MOA** · [ACL 2026 Main](https://aclanthology.org/2026.acl-long.531/) | 从 RoleMRC/OpenCharacter 构造约 310K SFT、20K RL 数据，联合三种目标和冲突处理。主要测角色、指令和交互质量的权衡。 | 相同底座 SFT、普通 GRPO、thought/off-policy/多目标消融；不是只比较不同模型排行榜。 | **实查**[仓库](https://github.com/ChonghuaLiao/MOA)有 `src`、recipes、训练与评测目录，Apache-2.0；本次未确认论文 checkpoint。 |
| **B10 Consistently Simulating Human Personas with Multi-Turn RL** · [NeurIPS 2025 Main](https://papers.nips.cc/paper_files/paper/2025/hash/4c91443877f8388d8190c938ac5a4d4d-Abstract-Conference.html) | 约 39K 对话行，用于学生、客户、聊天等 persona 模拟；评价 10–60 轮一致性。行为一致性不能自动证明群体代表性或真实用户分布。 | SFT、KTO、多轮 PPO；相同任务、初始人设、伙伴模型与对话长度。 | [代码](https://github.com/abdulhaim/consistent-LLMs)项目可见 OpenRLHF 扩展说明；未完成全部资产和 checkpoint 核验，标为**项目页/部分代码**。 |
| **B11 iStar** · [ICLR 2026](https://openreview.net/forum?id=ooROvpmxMV) | 用轨迹偏好学习隐式逐步奖励，实验覆盖 WebShop、VisualSokoban、SOTOPIA；角色/社交证据主要来自 SOTOPIA，另两项不应算作角色忠实评测。 | PPO、GRPO、轨迹偏好训练；固定强伙伴、自对话等伙伴条件会改变任务难度。 | **实查**[CharacterRL-iStar 目录](https://github.com/Tongyi-ConvAI/Qwen-Character/tree/main/CharacterRL-iStar)存在；未安装环境、执行训练或验证所有环境版本。 |
| **B12 LSH-RL / PersonaArena** · [EMNLP 2026 Findings](https://aclanthology.org/2026.findings-emnlp.1619/) | PersonaArena 1,000 个 persona，800 训练、200 测试；每场 3–4 个角色，联合局部与整段轨迹奖励。动作是叙事行为，不能当作 3D 游戏中已执行动作。 | DPO、对话 RL、全互动 RL、长期奖励和门控消融；episode-only 比较仅有小子集。 | [论文所给仓库](https://github.com/Shiwenlong-source/LSH-RL)本次访问失败；代码、PersonaArena 全数据与权重均记**待核**，不据论文实验表推定已经下载可用。 |
| **B13 OSPD** · [EMNLP 2026 Main](https://aclanthology.org/2026.emnlp-main.2105/) | 学生约 100-token 简人设、教师约 2,000-token 全人设；20/40 轮 on-policy 自蒸馏、60 轮评价，使用 CoSER/Beyond Dialogue。测的是短提示部署时的保持。 | 相同简人设的 SFT、off-policy 蒸馏、多轮 RL；与推理时拿完整 profile 的模型不直接等价。 | **实查**[参考实现](https://github.com/airaer1998/OSPD)；README 明确不分发上游数据、论文评价 harness 和 checkpoint，且打包环境未端到端执行 GPU 训练。存在外部 profile builder/PCV 调用，不能称无外部模型依赖。 |
| **B14 KuaiRP** · [arXiv 2026-09](https://arxiv.org/abs/2609.11127) | 12 原著角色、13 衍生角色，并区分玩家性别；Qwen3-4B/8B 的领域 SFT、RL 与能力保持蒸馏。TRACEbench 与 BFCL 分别涉及领域角色和工具能力，不能合并成通用角色智力分数。 | 同底座领域训练前后、SFT/RL/蒸馏阶段；世界知识与一般能力分别比较。 | [作者项目页](https://kuaishou-gamemind.github.io/projects/kuairp/)提供报告和结果；本次未确认完整训练数据、代码、模型权重，属于工业技术报告资源。 |

## 4. 角色质量、心理访谈、复合指令与角色控制

### 4.1 人格与回复质量评测

| 资源与论文 | 任务、规模与测量边界 | 可比较基线家族 | 实际发布情况 |
| --- | --- | --- | --- |
| **C01 InCharacter** · [ACL 2024 Main](https://aclanthology.org/2024.acl-long.102/) | 32 个角色、14 类量表的开放式心理访谈；以读者/专家给定人物标签作参照。量表覆盖人格、态度和情绪能力等多个构念，分数不等于临床人格真值。 | 直接自陈、开放访谈、经验回忆；描述、记忆库或二者组合；不同采访与评分协议。 | **实查**[代码、问卷和标签](https://github.com/Neph0s/InCharacter)，MIT；原量表及上游角色材料的条件需单独看，不能由仓库许可推断全部素材可商用。 |
| **C02 CharacterEval / CharacterRM** · [ACL 2024 Main](https://aclanthology.org/2024.acl-long.638/) | 中文 77 角色、1,785 段对话，4 类、13 项指标；论文写 11,376 个评价样例，当前 README 写 23,020，统计单位/版本需对应。主要是给定历史后的回复评价，划分单位不是完整对话。 | 通用/角色专用模型、LLM judge、CharacterRM；长度偏好与维度权衡不能由一个总分消除。 | **实查**[仓库](https://github.com/morecry/CharacterEval)有数据、评分代码和 RM 训练数据，MIT 代码；README 提供 CharacterRM 权重链接，本次未逐分片核验。正式 venue 是 ACL，非 EMNLP。 |
| **C03 RoleMRC** · [ACL 2025 Findings](https://aclanthology.org/2025.findings-acl.1082/) | 10,200 个 profile、37,900 条训练指令、约 1,400 测试样例；结合角色扮演、格式/优先级指令与阅读理解。部分自由对话约 9 轮，整体平均约 3.5 轮；MRC 不是长期自主记忆。 | 原底座、SFT、DPO、混入一般指令数据；角色任务与九类通用测试分别观察。 | **实查**[代码](https://github.com/LuJunru/RoleMRC)，MIT；[HF 数据](https://huggingface.co/datasets/Junrulu/RoleMRC)、[模型集合](https://huggingface.co/collections/Junrulu/rolemrc-67b2a4477a49eaea082ad33b)有公开入口，未核完所有权重文件。 |
| **C04 PersonaGym** · [EMNLP 2025 Findings](https://aclanthology.org/2025.findings-emnlp.368/) | 200 persona × 5 任务 × 10 问题，约 10K 评价问题，环境池 150 个文本场景。问题动态生成，GPT-4o 与 Llama-3-70B 评审；这不等同于长期自由互动环境。 | 相同人设和问题的通用/角色模型、不同 persona prompting；需区分全量与 Light 协议、生成问题版本。 | [代码项目](https://github.com/vsamuel2003/PersonaGym)页面已确认，本次未完成全数据和可运行流程的文件级审计。动态问题生成依赖外部模型及其版本。 |
| **C05 RAIDEN / RPCAJudger** · [COLING 2025 Main](https://aclanthology.org/2025.coling-main.735/) | 原论文池为 135 个中文角色、1,350 段对话、40,518 条 utterance、20,830 评价轮；11 维固定历史 pairwise 评价。**105 训练角色私有，30 测试角色公开**，不能把整池写成可下载。 | 相同固定上下文下的角色模型、LLM judge 与训练得到的 pairwise judge；不测 agent 生成整段历史的表现。 | [仓库](https://github.com/FrontierLabs/RAIDEN)、[RPCAJudger](https://huggingface.co/FrontierLab/RPCAJudger)公开入口；训练/测试公开范围按作者说明区分。代码 MIT，数据 CC BY-NC 4.0，许可不能互换。 |
| **C06 FURINA** · [arXiv v3，2026-04](https://arxiv.org/abs/2510.06800) | 20 个目标角色，按语言及已知/原创组合；1,471 个其他角色、1,459 段群体对话、7,181 测试 utterance，场景池来自 180 本书的 6,556 片段。测固定群聊历史的下一句，非 on-policy 群体互动。 | 同输入场景和人设的通用/角色模型；维度提示与评审偏置控制。熟悉角色优势依赖任务和人设信息量。 | **实查**[数据](https://huggingface.co/datasets/Tsumugii/FURINA)有中英文件与场景池；完整构建代码待核。本次未确认 ICLR 2026 正式记录，按已核实 arXiv 版本标注。 |

### 4.2 人设粒度、参数共享与可解释控制资源

| 资源与论文 | 任务、规模与测量边界 | 可比较基线家族 | 实际发布情况 |
| --- | --- | --- | --- |
| **C07 Profile Axes / FACD** · [EMNLP 2026 Main](https://aclanthology.org/2026.emnlp-main.1590/) | 211 个 profile：109 已知角色、102 合成角色，5 大维度、28 字段；语义匹配的结构化/非结构化人设，约 550–620 词、135–160 个事实。评测用 PersonaGym 与改造的 18 轮、3 角色 CoSER。 | 已知/原创、结构化/自然文本、完整/去敏感字段的匹配条件；FACD 与原提示对照。丰富信息下的结果不能外推到极短人设。 | **实查**[仓库](https://github.com/yonghyun010102/RPA_Bottleneck)约 300 文件，含 211 profiles 与评测；存在 corrected/legacy CoSER 分组映射，版本必须对应。MIT 代码，上游 benchmark 条款另计；无需专用训练权重。 |
| **C08 APC / Global Faithfulness** · [NeurIPS 2024 Main](https://proceedings.neurips.cc/paper_files/paper/2024/hash/309cadc33589efca4018a490c07db263-Abstract-Conference.html) | 3 个原创角色分别 8/19/30 条设定、各 10 问；6 个已知角色有 77–599 条设定。约 8.4K 相关性、18.9K NLI 训练数据；评分是逐项软约束，不是严格不矛盾证明。 | 全 profile、top-5 RAG、经历上传、APC 筛选偏好后 DPO；同底座和评分器训练范围。 | **实查**[代码](https://github.com/KomeijiForce/Active_Passive_Constraint_Koishiday_2024)、[相关性数据](https://huggingface.co/datasets/KomeijiForce/role-playing-apc-relevance)、[NLI 数据](https://huggingface.co/datasets/KomeijiForce/role-playing-apc-nli)及[相关性](https://huggingface.co/KomeijiForce/deberta-v3-large-relevance-12character)/[NLI](https://huggingface.co/KomeijiForce/deberta-v3-large-nli-12character)权重。公开默认 `12character` 判别器与论文三角色训练评价器不同；角色 LoRA 待核。 |
| **C09 Neeko** · [EMNLP 2024 Main](https://aclanthology.org/2024.emnlp-main.697/) | 在 Character-LLM 9 角色上做动态分块 LoRA 与路由，含 8+1 增量角色设置；测共享参数、角色切换和增量适应，不是上千 NPC 同时运行压力测试。 | 每角色独立微调、普通共享 LoRA、动态路由及 Fusion/Expansion 消融；参数和服务成本需分别计算。 | **实查**[仓库](https://github.com/weiyifan1023/Neeko)有 data、eval、moelora、训练与推理代码，Apache-2.0；完整论文权重未逐项核验。 |
| **C10 TraitBasis / τ-Trait** · [ACL 2026 Main](https://aclanthology.org/2026.acl-long.1743/) | 以不耐烦、困惑、怀疑、不连贯四种用户倾向及二者组合测试客服 agent；约 10 轮模拟。用隐藏状态方向控制倾向，不能写成已经实现任意 NPC 人格或 SAE 解释。 | 无 trait、提示控制、SFT/LoRA、激活控制；任务成功与 trait 表达分别观察。 | **实查**[τ-Trait](https://github.com/collinear-ai/tau-trait)有 tasks/tools/run/trajectories，MIT；默认 trait user 依赖 Collinear STEER API，整套 TraitBasis 服务并非已核实可离线复现。 |
| **C11 Codifying Character Logic** · [NeurIPS 2025 Main 正式论文](https://papers.neurips.cc/paper_files/paper/2025/hash/15294ba2dcfb4521274f7aa1c26f4dd4-Abstract-Conference.html) · [预印本](https://arxiv.org/abs/2505.07705) | 6 部作品、83 角色、5,141 场景；把人设转为 Python 判断逻辑，辅以语义 checker，做离线下一动作与 Best@K。代码演进部分会用参考动作更新，不是无需真值的在线自我修正。 | 完整文本人设、RICL、SFT、代码化人设；同场景信息、候选数量与动作评估器。 | **实查**[代码](https://github.com/KomeijiForce/Codified_Profile_Koishiday_2025)、[Fandom Benchmark](https://huggingface.co/datasets/KomeijiForce/Fandom_Benchmark)、[20,759 条 Check Scenes](https://huggingface.co/datasets/KomeijiForce/Check_Scenes)及[checker](https://huggingface.co/KomeijiForce/deberta-v3-base-check-scene)；[代码化 profiles](https://huggingface.co/datasets/KomeijiForce/Fandom_Codified_Profiles)有公开入口。 |
| **C12 Codified Decision Tree / CDT** · [ACL 2026 Main](https://aclanthology.org/2026.acl-long.568/) | Fandom 45 角色、20,778 对场景/动作；Bandori 40 角色、7,866 对，按时间前半训练后半测试。另有 77,182 事件；生成决策树与解释，仍主要是离线预测。 | vanilla、SFT、RICL、ETA、人工 profile、代码化人工 profile；时间切分与预训练原作知识需分开。 | **实查**[代码与预构建 packages](https://github.com/KomeijiForce/Codified_Decision_Tree)，约 110 文件；[Fandom](https://huggingface.co/datasets/KomeijiForce/Fine_Grained_Fandom_Benchmark_Action_Sequences)与[Bandori](https://huggingface.co/datasets/KomeijiForce/Bandori_Conversational_Benchmark_Action_Sequences)有实际 parquet。预建决策树不是新的 LLM checkpoint。 |

### 4.3 动态多轮的角色质量评测

| 资源与论文 | 任务、规模与测量边界 | 可比较基线家族 | 实际发布情况 |
| --- | --- | --- | --- |
| **C13 DMT-RoleBench** · [AAAI 2025 Main](https://ojs.aaai.org/index.php/AAAI/article/view/34768) | 996 个中文 seed、6 类角色、7 种访谈意图、3 种提示形式、14 项指标。GPT-4-Turbo 访谈者依据被测模型回答继续提问，属于真实 target-response 闭环；Qwen2-7B DMT-RM 逐轮二值评判。与 RoleLLM 的 RoleBench 是不同资源。 | 相同访谈者、seed 和轮数的通用/角色模型与 agent；DMT-RM 与人工/LLM 评分关系。动态 rollout 不自动覆盖跨会话长期关系。 | **实查**[官方仓库](https://github.com/DMT-RoleBench/DMT-RoleBench)只有 LICENSE 与 Coming soon；seed、标注细节和 RM 权重本次未核到公开文件，不能列为已可直接运行的测试包。 |

## 5. 时间、知识权限、记忆、情绪与关系

本节把“能正确回答事实”“知道此人何时知道什么”“记忆如何被使用”“角色处于哪个发展阶段”“关系如何影响互动”分开。它们可以共享原作或对话历史，但不存在一个替代全部能力的统一 memory score。

### 5.1 角色时点、私有信息与他人心智

| 资源与论文 | 任务、规模与测量边界 | 可比较基线家族 | 实际发布情况 |
| --- | --- | --- | --- |
| **D01 TimeChara** · [ACL 2024 Findings](https://aclanthology.org/2024.findings-acl.197/) | 4 部小说、14 角色、219 个角色时间点、10,895 样例；主实验均衡抽样 600 例，另有全库结果。覆盖 future、past-absence、past-presence、past-only；不在场主要限制声称亲历，不等于永远无法经转述获知。 | 提示/CoT/self-refine、普通 RAG、按时间截断 RAG、Narrative-Experts；不同方法得到的原作信息量需对齐。 | **实查**[代码](https://github.com/ahnjaewoo/timechara)与[数据](https://huggingface.co/datasets/ahnpersie/timechara)。代码 MIT，小说来源和数据研究/非商业条件另看；数据公开不解除原作权利。 |
| **D02 The Curse of Knowledge in Role-Playing Language Models** · [arXiv 2026-10](https://arxiv.org/abs/2610.17327) | 480 个成对场景实例，以隐藏事实/反事实孪生情景区分泄漏与猜测；涉及可见性、私信、听觉可及性，但输入是文本世界状态，不是传感器 benchmark。覆盖多种开放与闭源模型，不能写成所有模型必然失败。 | 全状态输入、不同 profile/layout、思考提示、由引擎生成的角色可见观察；后者依赖正确权限元数据。 | [作者解释](https://1npc.github.io/blog/2026/curse-of-knowledge-in-role-play/)；论文给出[匿名代码](https://anonymous.4open.science/r/curse-of-knowledge-roleplay-B8C6)，本次未完成文件审计。短模板场景的规则评分不能代替长剧情知识传播验证。 |
| **D03 REVERIEMEM / KBF-QA** · [arXiv 2026-06](https://arxiv.org/abs/2606.25632) | 8 本小说、4,386 道知识边界选择题，其中 2,442 可答、1,944 应拒答；另用 BookWorld 226 脚本。分层记忆记录角色可见事件、事实与人格；检索过滤不保证参数中的秘密知识不影响生成。 | RAG、RAPTOR、HippoRAG、ComoRAG、BookWorld；应答/拒答分别计分。 | [作者发表页](https://raids-lab.com/publications/tang2026staying/?r=tp)可核论文，本次未确认独立代码或 KBF-QA 下载入口；标为**论文自述/待核**。不是已核实正式会议论文。 |
| **D04 ToMATO** · [AAAI 2025 Main](https://ojs.aaai.org/index.php/AAAI/article/view/32143) | **实查 5,401 题**：一阶 2,676、二阶 2,725；false-belief 806 题是二阶子集，不能另加。753 段对话、15 种人格模式，每段 16 utterance；观察者在固定对话上答选择题，输入可含被问时点之后的对话。合成私有思想是标签来源，不是真实心智真值。 | 同对话/选项的 LLM、直接回答与推理提示；一阶、二阶、错误信念分别比较。不能据此替代被测 NPC 在线管理自己与他人的信念。 | **实查**[代码与 4 个 JSON](https://github.com/nttmdlab-nlp/ToMATO)。数据采用 META LLAMA 3 条件且 README 要求仅评价、不作 SFT；代码为 NTT 非商业内部研究/评价许可。静态检查发现数据 `conversation` 与脚本 `transcript` 等不一致，未运行修复，不能称开箱可复现。 |

### 5.2 原作 grounding、时间线与活跃故事记忆

| 资源与论文 | 任务、规模与测量边界 | 可比较基线家族 | 实际发布情况 |
| --- | --- | --- | --- |
| **D05 DREAM / TCM** · [KDD 2026 Main](https://doi.org/10.1145/3770855.3818027) · [论文](https://arxiv.org/abs/2608.05170) | TCM 为 20 本书、600 个时序/因果样例；另用 CoSER 100 本书与 LifeChoice 100 例子集。图从原作构建，动态的是查询与推理，不应写为已验证在线记忆持续更新。 | 普通 RAG、GraphRAG、GCA、CHARMAP；同原作文本、图构建信息和推理预算。 | **实查**[仓库](https://github.com/xzh-buaa/DREAM_KDD_2026)仅 README 与 Apache-2.0 LICENSE；当前未见实现与 TCM 数据文件。正式会议论文不等于当前实现齐全。 |
| **D06 RoleAgent / RoleAgentBench** · [NeurIPS 2024 Datasets and Benchmarks](https://papers.nips.cc/paper_files/paper/2024/hash/5875aca1ef70285a35940afbbce0f9fb-Abstract-Datasets_and_Benchmarks_Track.html) | 中英 25 个剧本、128 个角色；观察、事件、要点、洞察的分层记忆，测知识判断、反应、回复、总结。主要为离线场景与原作 grounding，不等于持续开放世界社会仿真。 | profile、普通检索、分层记忆；同底座和同剧本信息范围。 | **实查**[RoleAgentBench](https://huggingface.co/datasets/RoleAgent/RoleAgentBench)有分层 JSON。独立官方实现与模型权重本次未确认；同名 GitHub 项目不能未经核对认定为论文代码。 |
| **D07 THEANINE / TeaFarm** · [NAACL 2025 Main](https://aclanthology.org/2025.naacl-long.435/) | 以时间线组织多会话记忆，保留历史而非简单覆盖。主要使用 MSC、CC 等 3–5 会话数据，TeaFarm 200 个误导/反事实历史问题。它是长期对话记忆邻接资源，不直接证明 NPC 人格或关系变化。 | 全历史、普通 RAG、递归摘要、记忆更新、MemoChat、COMEDY；历史长度与检索预算一致时才可比。 | **实查**[仓库](https://github.com/kimnamssya/Theanine)有约 19 个实现/示例文件；[TeaFarm](https://huggingface.co/datasets/LangAGI-Lab/teafarm)有作者入口。本次未见明确仓库 LICENSE，不能默认自由再分发全部内容。 |
| **D08 BOOKMARKS** · [arXiv 2026](https://arxiv.org/abs/2605.14169) | 当前标题为 Checkpoint-Accelerated Active Grounding；按概念、状态、行为维护活跃叙事与增量 checkpoint。最新版含 8 组测试及 284 道 Manosaba 选择题；主要测原作下一动作、Best@3 与选择题，非玩家分支世界的完整闭环。 | vanilla、检索示例、ETA、三路 ETA、记忆/checkpoint 消融；候选数及原作可见范围不可混淆。 | **实查**[仓库](https://github.com/KomeijiForce/BOOKMARKS_Koishiday_2026)有约 57 文件、19 个 JSON 与源代码；最新新增的全部选择题未确认包含在公开集。LICENSE 未见；冻结论文版本与资源版本尤其重要。 |

### 5.3 角色化记忆与“记忆如何用于回复”

| 资源与论文 | 任务、规模与测量边界 | 可比较基线家族 | 实际发布情况 |
| --- | --- | --- | --- |
| **D09 RoleMemo / DualMem** · [EMNLP 2026 Findings](https://aclanthology.org/2026.findings-emnlp.270/) | 2,052 persona、20,244 问题；训练/测试角色 1,914/138，问题 18,088/2,156。区分事实与角色主观 insight，32K 历史评价、256K 鲁棒性；主观标签和 RL 奖励含 LLM 判断。 | 相同 answerer、retriever 和 top-10 条件下的多种通用 memory 框架；事实召回与主观洞察分开。 | **实查**[仓库](https://github.com/Collab-Gen/RoleMemo)约 23 文件、部分实现；README 对完整数据集、checkpoint 与 RL agent 仍标 Coming soon。本次不能把 20,244 题写成已全部可下载。 |
| **D10 StratMem-Bench** · [ACL 2026 Main](https://aclanthology.org/2026.acl-long.1491/) | LoCoMo 衍生 657 题，每题平均给定 8.79 条候选记忆，分 Must/Nice/Irrelevant。测必要记忆识别、无关抑制与自然表达；检索结果已给定，不测上游写入、检索或遗忘。 | 同记忆池下不同 LLM、普通提示与记忆使用策略；不能把端到端 memory 系统优劣归结为该分数。 | **实查**[仓库](https://github.com/seucoin/StratMem-Bench)有 2 个数据 JSON 与 `me.py` 等约 6 文件，Apache-2.0；不需要新的 agent 权重。 |
| **D11 SubtleMemory** · [EMNLP 2026 Findings](https://aclanthology.org/2026.findings-emnlp.1199/) | 10 条历史，平均约 211.6K token、236 会话；1,522 问题、1,090 变体。考察互补事实、条件差异、矛盾的保留与推理；这里的 relational facts 是事实关系，不是 NPC 与玩家的人际关系。 | 6 类记忆系统、Claw 原生/插件配置、Gold-session oracle；固定历史回放后回答，不是让模型自行完成所有会话。 | **实查**[仓库](https://github.com/Yummytanmo/SubtleMemory)约 877 文件，包含 10 条历史的完整数据与代码，Apache-2.0；未执行各外部记忆系统。 |
| **D12 MRBench / MRPrompt** · [ACL 2026 Findings](https://aclanthology.org/2026.findings-acl.1175/) | 来自 10 英文、6 中文小说；每个能力家族各 200 英文、200 中文样例，4 种能力、8 项指标。考察给定 persona memory 后的锚定、选择、边界和行为表达，主要是提供上下文后的单轮回答。 | 同内容的 Base、Card、MRPrompt；提示组织与额外信息量要区分。 | [仓库](https://github.com/41522/MDRP)可见 MRPrompt/rubric 与数据说明，MIT；未完整核验全部文件树，按**部分实查/项目页**。不能据名称声称已测试参数记忆或长期外部记忆写入。 |

### 5.4 角色阶段、关系诊断、长轮保持与情绪

| 资源与论文 | 任务、规模与测量边界 | 可比较基线家族 | 实际发布情况 |
| --- | --- | --- | --- |
| **D13 ArcANE** · [EMNLP 2026 Main](https://aclanthology.org/2026.emnlp-main.1998/) | v2 原论文：19 本书、87 角色、570 个 arc、4,854 probes；主验证 5 本、25 角色、205 arcs、1,754 probes。同一人物不同阶段的倾向/行为/理由是核心，非真人关系闭环。 | identity-only、近期摘要、RAG、LifeChoice、TimeChara、正确 arc context；SFT/DPO/RL，负例包括同角色错误阶段。 | **实查**[代码](https://github.com/holi-lab/ArcANE)、[数据](https://huggingface.co/datasets/holi-lab/ArcANE-Data)、[5 个模型](https://huggingface.co/collections/holi-lab/arcane)。版权造成公开训练书 10 本而非论文 12 本、主测试 4 本而非 5 本；代码 MIT、标注 CC BY 4.0，原作文本不一并开放。 |
| **D14 REMP** · [EMNLP 2026 Findings](https://aclanthology.org/2026.findings-emnlp.602/) | 原论文 160 角色、80 对，历史平均约 60 会话、800 轮；1,195 个关系/情绪/记忆/persona 探针。被测模型在预先生成的长历史后完成诊断分支，并未自行生成此前全部 800 轮。 | 同历史、触发事件的多个 LLM；anchor/no-anchor judge；关系适应与静态人设保持分别观察。 | **实查**[仓库](https://github.com/DreamFragrance/REMP)约 29 文件，含评价代码和 **4 条示例轨迹**；完整 80 条轨迹本次未见。论文代码/数据许可声明与实际根目录 LICENSE 不完全对应，应按资产另核。 |
| **D15 Persistent Personas?** · [EACL 2026 Main](https://aclanthology.org/2026.eacl-long.246/) | 8 个角色、7 个模型、100+ 轮历史，在 10 个前缀位置用 BFI、RoleBench、IFBench、XSTest 等检测 persona fading、指令与安全。重点是上下文中的保持，不是人物应有的关系成长。 | persona/no-persona、访谈/目标任务、不同前缀长度；安全改善也可能同时反映人设消退，不能只看单维。 | [代码、数据与结果](https://github.com/peluz/persistent-personas)目录可见，MIT；未逐项审计全部资产和执行长轮轨迹。 |
| **D16 DynSess** · [EMNLP 2026 Findings](https://aclanthology.org/2026.findings-emnlp.689/) | 2,100 persona，2,000 训练、100 测试；10K 原始偏好对筛为 6,089 对。搜索最长 50 轮；评测是在 0–50 轮固定前缀后续写 10 轮，不能直接写为所有测试均从头生成 60 轮。 | SFT、随机合并偏好、搜索得到的会话偏好、DSPO/GSRPO；会话级 rubric 与静态逐轮分数不同。 | **实查**[仓库](https://github.com/Collab-Gen/DynSess)约 22 文件，含 100 条测试 seed、少量格式示例与评价脚本；README 明确完整约 512MB 训练数据和 checkpoint **未随仓库发布**，MIT 代码。 |
| **D17 MECoT** · [ACL 2025 Findings](https://aclanthology.org/2025.findings-acl.435/) | 使用 RAPD 与 DailyDialog，在二维效价–唤醒空间建模 12 个情绪状态，并让人格调节情绪转移。情绪状态标签是建模框架，不是对真实情绪的生理测量；不直接覆盖长期依恋或玩家关系。 | 无情绪推理、静态情绪条件、情绪转移/人格调节消融；同底座与同对话上下文。 | **实查**[仓库](https://github.com/turnwind/llmemochain)约 17 文件，含中英 JSON、角色 profile、模型与训练示例，MIT；独立训练权重本次未确认。 |
| **D18 PersMem** · [arXiv 2026-09](https://arxiv.org/abs/2609.34372) | 将人格条件映射到情绪评价、记忆保留与衰减、被动和主动检索。依恋实验有 165 条 held-out 记忆；Big Five 设置使用 50 个 profile、320 条合成记忆与 6 轮交互。人格控制规则经手工校准，短实验不等于心理机制验证或长期关系研究。 | 语义 RAG、随机检索、去除人格门控等控制；固定生成器与记忆池。引用的旧 CoSER baseline 与当前 judge 不同，不能直接横比为 SOTA。 | 论文全文已核读；本次未确认原作者公开代码、独立数据包或权重。相似名称的其他仓库不认作作者实现。属于方法与早期实验资源，不能列为已有即用 baseline。 |

## 6. 角色微调与安全评测

这些资源衡量角色条件下的安全退化和缓解，不提供所有情境的安全保证。反派的虚构价值观、角色语言风格和现实危害性请求是不同评价对象；安全分数与角色分数应保留各自含义。

| 资源与论文 | 任务、规模与测量边界 | 可比较基线家族 | 实际发布情况 |
| --- | --- | --- | --- |
| **E01 SaRFT / Beware of Your Po!** · [ACL 2025 Main](https://aclanthology.org/2025.acl-long.544/) | 风险分析涉及 95 角色，方法验证使用 10 角色、3 底座；安全测试包含 AdvBench 520、HEx-PHI 330、Beaver 1,000。角色指标有 ROUGE 等，不能据此推出沉浸与人格细节完全无损。 | 普通角色 SFT、SEAL、SafeInstr、Vaccine、SPPFT、SafeLoRA 等；全量微调/LoRA 与训练预算需匹配。 | **实查**[代码](https://github.com/yulinlp/SaRFT)有训练、解码、评测及评价数据目录；许可证和作者 checkpoint 本次未确认，数据上游条件单独适用。 |
| **E02 MD-Trace / MD-Shield** · [ACL 2026 Findings](https://aclanthology.org/2026.findings-acl.349/) | 80 角色、400 个静态案例；MD-Shield 使用 180 个 SFT 样例并混入良性数据。区分任务、身份、场景压力，推理 trace 与最终行为关联不证明内部道德机制或 CoT 忠实性。 | task/identity/scenario 拆分，STAR-1、RealSafe、SafePath 等推理安全方法；同请求条件与角色要求。 | **实查**[仓库](https://github.com/lavapapa/MoralJustify)有 MIT 流水线与少量示例；论文说明未完整释放攻击集，完整训练权重未确认。不能据小样例宣称整个测试集合公开。 |
| **E03 RoleCDE** · [ACL 2026 Findings](https://aclanthology.org/2026.findings-acl.106/) | 正式 PDF 为 7,957 个 role–scenario、23,871 个三难度 dilemma，8 类职业/社会角色；Anthology 摘要的约 240K 与 PDF 不一致。单轮二选一加理由，测 RF/RC/AC/AF；DBR 是角色侧选择率，不是普遍质量分或安全率。 | 原底座、CoT、同底座 SFT/DPO；角色义务与通用规范冲突需保留具体语境。1,000 个人类样例比较的是类别分布，不是逐题正确率。 | **实查**[仓库](https://github.com/rabbitrose/RoleCDE)递归文件树：986 个 persona JSON、5 个评价脚本、4 个训练/合并脚本及样例输出；公开子集不等于论文 7,957 个组合的全池，未核到权重，未复现实验。此项讨论规范冲突，不与现实危害性请求测试混为一类。 |

## 7. 社会交互、互动叙事与可执行游戏环境

环境的反馈机制决定指标含义：固定对白测试、由 LLM 叙述状态的舞台、结构化文字游戏和真实引擎中执行动作，提供的证据不同。以下资源因此分组，不能只凭“多 agent”“NPC”“embodied”等名称合并比较。

### 7.1 世界状态、群落运行与规则游戏

| 资源与论文 | 任务、规模与测量边界 | 可比较基线家族 | 实际发布情况 |
| --- | --- | --- | --- |
| **F01 LIGHT** · [EMNLP-IJCNLP 2019](https://aclanthology.org/D19-1062/) | 幻想文字世界中的人物、地点、物品、对白、动作和表情，含 get/give/wear 等可执行动作。原始论文的下一回复/动作任务与后续任务环境须区分；当前 WILD 扩展有 41,131 个训练 episode，**不是 2019 原始论文规模**。 | 对话检索/生成、移除世界信息、加入完整世界状态、动作合法性过滤；任务成功与风格表现分开。 | [LIGHT/ParlAI 项目](https://www.parl.ai/projects/light/)给出 `light_dialog`、`light_dialog_wild`、quest、ATOMIC-LIGHT 下载与 BERT baseline 命令；项目资源已核，未运行环境或训练。 |
| **F02 Generative Agents** · [UIST 2023](https://doi.org/10.1145/3586183.3606763) · [论文](https://arxiv.org/abs/2304.03442) | 25 个 agent、两天游戏时间的小镇；记忆、反思、计划和社会事件传播。部分组件评价是回放访谈式消融，不是每个反事实配置都重跑整段社会历史。 | 无记忆/反思/计划的组件条件，人工与 agent 访谈评价；社区结果不能仅由单人访谈分数推出。 | [sandbox 与回放代码](https://github.com/joonspk-research/generative_agents)公开，运行依赖外部 LLM/API；不是一个可下载的专属 NPC 预训练权重包。 |
| **F03 Project Sid / PIANO** · [arXiv 2024 技术报告](https://arxiv.org/abs/2411.00114) | Minecraft 中并行模块和多时间尺度运行；部分文化分析使用 500 agents、9,000 秒。报告讨论上千规模，但服务器稳定性及预设制度限制了“文明涌现”解释。 | PIANO 组件、并行机制、认知模块等报告内比较；规模、tick、API、硬件和延迟条件都是系统指标的一部分。 | **实查**[仓库](https://github.com/altera-al/project-sid)只有 PDF、README 和图片；完整 PIANO runner、Minecraft 配置、日志与公开 benchmark 未确认。不能列为已开放的千 agent 复现实验平台。 |
| **F04 Setting the DC** · [NeurIPS 2025 GenProCC Workshop](https://genprocc.github.io/) · [论文入口](https://openreview.net/pdf?id=3Op7kJOvaD) | D&D 工具执行、参数、表演、战术、状态和效率等维度；规则战斗能力与完整长期 campaign 是不同对象。本次全文获取受 403/verification 限制，仅完成会议及作者元数据核查。 | 同规则、同工具接口的 LLM agent；战术、合法性和角色表现不能合为一个分数。 | [作者发表页](https://zhu.codes/)可确认；专属环境代码待核。**是 workshop，非 NeurIPS Main**；不能以另一个 withdrawn 投稿版本补充正式录用身份。 |
| **F05 CriticaLLM** · [arXiv 2026-10](https://arxiv.org/abs/2610.21525) | 简化 D&D 的三个房间，GM、Judge 和地图状态组件；包含 9 位专家、11 类规则绕过问题。人工体验条件与自动指标不完全同构，不是无限开放 campaign。 | 相同游戏规则下的 GM/合法性检查组件与模型配置；规则服从、叙事和玩家体验分别解释。 | 论文指向[代码](https://github.com/Juvwh/RPG_With_LLM)，本次工具访问受限，只确认作者公开声明，未核到文件树；无专属训练权重需求不表示运行零依赖。 |

### 7.2 导演、演员与场景推进

| 资源与论文 | 任务、规模与测量边界 | 可比较基线家族 | 实际发布情况 |
| --- | --- | --- | --- |
| **F06 IBSEN** · [ACL 2024 Main](https://aclanthology.org/2024.acl-long.88/) | 导演–演员协作的可控互动戏剧；改编剧本含 7 幕、14 个目标、10 次运行，约 9 轮超时后可强制推进。角色行动主要为文本，不是物理模拟器执行。 | 无导演演员、直接脚本/导演控制、分工协作；目标达成与自由交互需同时保留解释。 | **实查**[仓库](https://github.com/OpenDFM/ibsen)有 data、server、frontend 和依赖文件，MIT；终端与前端是运行接口，不需要论文专属训练权重。 |
| **F07 HAMLET** · [ICLR 2026](https://iclr.cc/virtual/2026/poster/10009957) · [论文](https://arxiv.org/abs/2507.15518) | 分层场景蓝图、planner/transfer/advancer 与 narrator，涉及 100 个主题；PAD-8B 选择 Fast/Slow/Silence/Action。主 PAD 定量测试未包含 Action，不能将“embodied”直接解释为完整动作控制已验证。 | IBSEN、导演/演员协作、planner/advancer/PAD 组件；场景叙述与可执行世界分开。 | **实查**[仓库](https://github.com/Tsumugii24/HAMLET)只有 README 与图片；[HF 数据页](https://huggingface.co/datasets/Tsumugii/HAMLET)当时显示 empty、约 5.25KB。代码、训练集、权重不能标为已完整发布。 |
| **F08 AdaMARP** · [ACL 2026 Findings](https://aclanthology.org/2026.findings-acl.1563/) | actor 与自适应 scene manager；AdaRPSet、AdaSMSet 分别支撑角色与场景管理，AdaptiveBench 测约 20 轮的选角、切场、加角、结束。论文/项目版本的规模统计不同，本表不合并混报。 | 固定 cast、无自适应场景管理、actor/scene-manager 消融；场景控制和角色质量分开。 | [项目](https://xuzhenhua55.github.io/AdaMARP/)、[代码](https://github.com/Xuzhenhua55/AdaMARP)可见实现与 Git LFS 数据路径；未完整拉取 LFS 资产，不据指针文件确认全部训练数据已取得。 |

### 7.3 社交能力、目标冲突与信息不对称

| 资源与论文 | 任务、规模与测量边界 | 可比较基线家族 | 实际发布情况 |
| --- | --- | --- | --- |
| **F09 SocialBench** · [ACL 2024 Findings](https://aclanthology.org/2024.findings-acl.125/) | 约 500 个中英角色；个体与群体语境中的知识、风格、情绪、记忆、社交理解。大量任务是给定上下文的选择/回忆，不能由此断言长时间群聊出现因果性的从众漂移。 | 通用 LLM、角色模型、相同上下文的提示/推理策略；各维度独立报告。 | **实查**[数据与评价代码](https://github.com/X-PLUG/SocialBench)；作为 benchmark，不要求同时提供新的 agent 权重。 |
| **F10 SOTOPIA** · [ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/b3075b88e583a0e98d8b24338a613060-Abstract-Conference.html) | 40 个角色、90 场景、每场 5 对角色配置，即 450 任务；通常两名 agent、最多约 20 轮。7 维社交评价包含目标等内容，目标达成不等同于忠实扮演文学人物。 | 固定伙伴、自对话、不同模型配对；同私有目标、背景、judge 与轮数上限。 | [环境代码](https://github.com/sotopia-lab/sotopia)、[数据](https://huggingface.co/datasets/cmu-lti/sotopia)公开；环境/场景存在已核，API 与包版本影响运行，未执行复现。 |
| **F11 SOTOPIA-π** · [ACL 2024 Main](https://aclanthology.org/2024.acl-long.698/) | 用 SOTOPIA 互动轨迹做行为克隆（BC）和优质 rollout 筛选后的 self-reinforcement（SR）。这里的 SR 是再次监督训练，不能仅凭名称写成 PPO。 | 原模型、BC、SR、BC+SR；固定强伙伴和人工/自动评审要区分。 | **实查**[代码](https://github.com/sotopia-lab/sotopia-pi)有生成、训练、人评流程；[数据](https://huggingface.co/datasets/cmu-lti/sotopia-pi)、[BC+SR 权重](https://huggingface.co/cmu-lti/sotopia-pi-mistral-7b-BC_SR)为公开入口，未重跑各训练配置。 |
| **F12 SOTOPIA-Ω** · [ACL 2025 Main](https://aclanthology.org/2025.acl-long.1203/) | 以 native、perspective-taking、slow strategy 生成训练数据，再做 SFT；加入逐轮策略遵循维度。训练数据中的慢推理不意味着部署时每轮都执行同等思考。 | π、BC、不同策略数据与策略注入消融；目标得分与社交指令遵循分开。 | **实查**[仓库](https://github.com/WYRipple/SOTOPIA-Omega)有生成和训练脚本；[数据](https://huggingface.co/datasets/WYRipple/sotopia-omega)、[模型集合](https://huggingface.co/collections/WYRipple/sotopia-checkpoints-683527f070d215849adc2873)有入口。未逐个加载 checkpoint。 |
| **F13 Lifelong-SOTOPIA** · [arXiv 2025](https://arxiv.org/abs/2506.12666) | 同一对 agent 连续约 40 个 episode；随机场景对历史依赖可能较弱，另有 5 个手工历史依赖案例。跨 episode 不等于模型持续更新参数或真实人类长期关系。 | 全历史、递归总结；固定 agent pair、目标和场景次序。 | 专属代码、完整长期测试场景本次未确认。基础 SOTOPIA 已开源，不能据此推定本论文新增的 longitudinal 协议与数据也已全部发布。 |
| **F14 SOTOPIA-TOM** · [COLM 2026](https://proceedings.colm.cc/paper_files/paper/2026) · [论文](https://arxiv.org/abs/2605.02307) | 160 个人审场景、600 个 silver 场景，3–5 个 agent；公开发言与按接收者过滤的私信，测披露、询问、隐私和效率。显式信息权限比自由隐藏动机更容易核对。 | ToM-Coach、ToM-Belief、Self-Focused 等提示条件；信息可见范围与思考预算相同才可比。 | **实查**[HF 数据](https://huggingface.co/datasets/yashwanthys/sotopia-tom)有场景行；论文代码指向 [SOTOPIA](https://github.com/sotopia-lab/sotopia/)。无需新增专属权重，不表示能跳过环境版本核对。 |

## 8. 多模态：图像、视频、语音与表演

多模态角色化至少涉及三种不同任务：依据视觉场景产生角色反应、根据语音和文本共同组织内容、以及在台词已给定时表现声音与情绪。可下载的图片/视频/音频也必须与标注分开核验；尤其影视原片经常不随标注公开。

| 资源与论文 | 任务、规模与测量边界 | 可比较基线家族 | 实际发布情况 |
| --- | --- | --- | --- |
| **G01 MMRole** · [ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/a5c7206fd66e8314bb21a04492359353-Abstract-Conference.html) | 85 角色，72 训练、13 未见；11,032 图像、14,346 对话、85,456 训练样本；测试 216 ID、78 OOD。主要按固定参考历史预测下一轮，不是自由长期视觉互动。 | Qwen-VL-Chat+profile、多模态角色 SFT、角色评审 RM；同图像、人设与历史。 | **实查**[仓库](https://github.com/YanqiDai/MMRole)有训练/评测脚本，MIT；README 提供 MMRole_dataset、MMRole-Agent、MMRole-Eval_RM 的 HF 入口。未逐一核完权重；COCO 图片需从上游另取。 |
| **G02 Video2Roleplay** · [EMNLP 2025 Main](https://aclanthology.org/2025.emnlp-main.1209/) | 论文报告约 60K 视频、700K 对话，57K/3K 视频划分，并以 328 个精选问题等评价；InternVL2.5-8B LoRA。离线选帧的视频理解不等于实时连续视觉控制。 | 纯文本、普通视频 VLM、角色 SFT、不同帧选择；相同视频信息和测试角色。 | **实查**[仓库](https://github.com/zxqSled/Video2Roleplay)仅 README/License，标 Coming soon；论文的 60K 视频资源、完整代码和模型未核到实际发布。 |
| **G03 CAVI / Through the Lens of Character** · [arXiv 2026-05](https://arxiv.org/abs/2605.09443) | 在 MMRole 和两个 VLM 底座上干预视觉表示/注意力，缓解视觉与角色条件干扰。不是新建可执行具身环境，也不是任意视觉性格调节的普遍证明。 | 原 VLM、角色提示、不同激活干预/剪枝配置；共用 MMRole 划分。 | 全文中未核到作者公开代码/权重入口；使用的 MMRole 资源已存在。正式会议状态待核，保留 arXiv，不把已有数据等同于本方法可复现。 |
| **G04 OmniCharacter** · [ACL 2025 Main](https://aclanthology.org/2025.acl-long.1276/) | 20 个《原神》角色、10,072 对话、约 135K 音频、375 小时，主要由 TTS 构造，同角色划分。测文本与声音身份/表达；报告的 289ms 是特定语音环节，不覆盖全双工端到端延迟。 | 一般文本/语音模型、多说话人 TTS、角色语音联合模型；声音相似与人格忠实分开。 | [代码](https://github.com/zchoi/OmniCharacter)、[数据](https://huggingface.co/datasets/Tongyi-ConvAI/OmniCharacter)有公开训练/推理说明；权重未逐文件核验。合成音频规模不能写成人类自然对话录音规模。 |
| **G05 OmniCharacter++** · [TPAMI 2026](https://ieeexplore.ieee.org/abstract/document/11506238) · [项目](https://zchoi.github.io/OmniCharacter-plus/) | 作者/资源页报告 10K+ 角色、118K 对话、约 1M 语音。此次只完成新版本元数据与资源核查，未将其列作全文方法精读；不据页面结果延伸方法因果结论。 | 原 OmniCharacter、通用多模态语音、角色条件语音等家族；新增规模与独立测试划分需对应新版论文。 | **实查**[代码入口](https://github.com/zchoi/OmniCharacter-plus)、[约 550GB 数据文件列表](https://huggingface.co/datasets/haonanzhang/OmniCharacter-plus)、[9B BF16 safetensors](https://huggingface.co/haonanzhang/OmniCharacter-plus)。未下载全数据；viewer 格式报错不等于文件不存在。README 的 CC BY-NC 4.0 与 HF 的 Apache-2.0 元数据冲突，不能替作者选定宽松许可。 |
| **G06 ActorMind** · [ACL 2026 Findings](https://aclanthology.org/2026.findings-acl.1718/) | Friends 第一季 24 集、7,653 utterance、313 场景、6 主角、约 5 小时 15 分钟；utterance 总数还含配角。11–14 集测试，其余提供参考；任务给定目标台词后生成表演语音，不是自主写出下一句。 | IndexTTS、CosyVoice2、F5-TTS、YourTTS、Qwen-Omni；同参考音频/台词。RP-MOS 将错误音色直接记低分，表演与声纹因素并非完全分离。 | **实查**[仓库](https://github.com/OzymandiasChen/ActorMind)有 24 集的 segment/scene/profile 标注；作者明确不分发 Friends 音频，未见完整 pipeline 或独立权重。标注公开不等于音频训练资产齐全。 |

## 9. 代码、数据、权重的发布状态横向核对

这一节是上述条目的交叉索引，不增加论文计数，也不是资源排名。一个无需训练的系统没有专属权重并不构成缺失；一个训练论文只提供训练数据，则与可加载 checkpoint 是不同发布层级。

| 已核到的发布形态 | 代表资源 | 实际能够确认的范围 |
| --- | --- | --- |
| 代码、实际数据、模型权重均有可检查资产 | CoSER、HER、ArcANE | 分别看 A04、B05、D13；仍有上游底座/API 依赖、公开子集与论文规模差异。没有独立重训或复算结论。 |
| 数据与判别器/结构化决策资产可检查 | APC、Codifying Character Logic、CDT | APC 是相关性/NLI 判别器；CDT 是预构建决策树。它们不能与一个新角色语言模型 checkpoint 混称。公开评分器训练范围还可能与论文不同。 |
| 数据文件明确，但完整训练实现或权重未齐全核实 | OpenCharacter、RolePersonality、RoleBench、VeriRole、FURINA | 每项资产范围不同：VeriRole 当前是 README+训练 JSON；FURINA 是评测数据；不能因均“有数据”就称相同复现成熟度。 |
| 代码和小样例可见，完整论文数据/权重尚未公开核实 | RoleMemo、DynSess、REMP、OSPD | RoleMemo 的完整数据与 RL agent 为 Coming soon；DynSess 不含完整约 512MB 训练集；REMP 只见 4 轨迹；OSPD 明确是参考实现而非论文全套包。 |
| 官方仓库存在，但当前主要为声明、图或论文 | DREAM、HAMLET、Video2Roleplay、Project Sid、DMT-RoleBench | 不能以 GitHub 链接数量衡量可运行程度。HAMLET 数据页当时为空；DREAM 有 LICENSE，但无实现文件；DMT 尚 Coming soon。 |
| 代码/场景可用，运行仍依赖外部服务或环境 | Generative Agents、SOTOPIA 系列、IBSEN、τ-Trait | API 版本、伙伴模型、judge、服务许可与环境版本进入实际复现条件；τ-Trait 默认依赖 STEER API。 |
| 标注可见而原始媒体不随之提供 | ActorMind、部分 ArcANE 原作内容、MMRole 上游图片 | Actors/角色的标注、小说原文、影视音轨和 COCO 资产各有来源；一个仓库许可证不覆盖所有上游内容。 |
| 有作者入口，但下载或方法资产尚待核验 | KuaiRP、REVERIEMEM、CAVI、LSH-RL、CriticaLLM、Setting the DC、Lifelong-SOTOPIA | 有的只公开报告，有的访问受限，有的未确认专属下载；本文保留这些原因，不把全部统一写成“未开源”。 |

### 9.1 版本与许可中的具体区别

**版本会改变数据规模与评测含义。** ArcANE 的论文池大于公开子集；CharacterEval 的论文与 README 样本统计不同；BOOKMARKS 更新了标题和测试任务；Profile Axes 发布了修正后的 CoSER 分组；APC 公开默认判别器的角色覆盖不同于论文主实验。这些差异都能造成“同名资源、不同测试”的情况，不能用一个总规模隐藏。

**代码许可、数据许可、原作权利与模型底座许可相互独立。** RAIDEN 的代码 MIT 不覆盖其 CC BY-NC 4.0 数据；ArcANE 的 MIT 代码和 CC BY 4.0 标注不包含原作全文；Character-LLM 的差分权重还依赖原底座；ToMATO 同时有数据用途限制和代码的非商业研究许可；OmniCharacter++ 当前许可声明冲突尚未解决。未见 LICENSE 的公开文件也不自动获得任意再分发许可。

**同源训练资产不应重复累计为独立证据。** ChARM/AAM 与 CPO 数据存在谱系关系；RAIDEN-R1 到 VeriRole 属版本演进；Character-R1 与 CRPO 都使用 CharacterBench 的 650 条训练子集；RolePersonality 继承 InCharacter 问卷；多个训练方法复用 RoleMRC、OpenCharacter 或 CoSER。按论文数量相加不能表示独立数据来源相同倍数增加。

## 10. 各类资源能支持的结论与尚未覆盖的部分

这不是实验计划，而是对现有测量对象的对照，便于阅读领域结论时识别证据范围。

| 被讨论的能力 | 已有对应资源类型 | 仍不能从这些分数直接推出的结论 |
| --- | --- | --- |
| 人设知识、语气、人格倾向 | RoleBench、CharacterEval、InCharacter、PersonaGym、RolePersonality | 真正形成内部人格、心理量表具有临床效度、在完整游戏过程中持续按该人格行动 |
| 指令与角色同时遵循 | RoleMRC、MOA、APC、FACD、RoleCDE | 所有目标可以无代价同时满足；NLI 或二选一标签是全情境唯一正确标准 |
| 此角色此时有权知道什么 | TimeChara、Curse of Knowledge、REVERIEMEM、SOTOPIA-TOM、ToMATO | 参数知识已被删除；完整复杂社会中的传播、误信、转述和不可靠叙述都已被验证 |
| 长历史记忆的写入、检索与使用 | THEANINE、RoleMemo、SubtleMemory、MRBench、StratMem | 每个 benchmark 都测了写入到使用的全链路；事实关系就是人际关系；给定记忆池的成功等于实际检索成功 |
| 角色随叙事阶段或关系变化 | ArcANE、REMP、MECoT、Lifelong-SOTOPIA | 对真实玩家持续数月的自然关系变化已被验证；静态历史后的诊断回答等于整个长期闭环 |
| 长轮一致性和互动质量 | GCA、DMT-RoleBench、DynSess、Persistent Personas、OSPD、LSH-RL | 相同轮数意味着相同条件；固定前缀、访谈者驱动、自由多方 rollout 的误差累积可以直接比较 |
| 社会目标、隐私和互动策略 | SOTOPIA 系列、SocialBench | 目标成功必然角色忠实；固定群聊下一句测试能证明群体长期从众或社会制度自然涌现 |
| 游戏行动和叙事控制 | LIGHT、Generative Agents、IBSEN、HAMLET、AdaMARP、Project Sid、D&D 相关系统 | 文本宣称的动作已由引擎合法执行；导演可控性、人类可玩性、规模吞吐是同一个指标 |
| 多模态角色表达 | MMRole、Video2Roleplay、OmniCharacter 系列、ActorMind | 图像问答等于具身控制；声音相似等于人格；单个语音模块延迟等于全双工实时 NPC 的端到端延迟 |
| 角色条件下的安全 | SaRFT、MD-Trace/MD-Shield、Persistent Personas | 静态攻击通过率能代表全部长程安全；拒答率上升必然同时保持角色质量 |

本文覆盖 **84 项数据、方法与评测资源**：原索引 75 项，本轮增加 8 项对应研究论文的资源及 1 项 Sony CPDC 官方挑战。现有资源涉及已正式发表工作、预印本、投稿稿及挑战数据，不能简单按资源链接数量计算可复现论文数量。综述、工程博客和各资源的方法分析见 [研究 Roadmap](../ROADMAP.md)；本文件侧重“公开资源究竟测什么、当前确实提供什么”。




## 11. 增补：玩家、角色状态与可执行世界的直接相关资源

这九项补充以 **player-facing role play** 为筛选条件，不把 VillagerAgent、MindCraft 或其他通用 Minecraft 任务协作框架算作角色忠实度 baseline。下表的“实查”仅指仓库文件树或实物资源存在，**不表示已运行或复现模型结果**。

| 资源／论文 | 与人物扮演的直接关系及实验边界 | 实际资源和可比较条件 |
| --- | --- | --- |
| **H01 CFSM / CPFSM** · [ICLR 2026](https://proceedings.iclr.cc/paper_files/paper/2026/hash/a862f5788fd09bb6843c694d8120d50c-Abstract-Conference.html) | 将人物状态、事件及转移逻辑显式化。合成简化 FSM 验证执行规则的准确率；Fandom 参考动作 NLI 与 Best@K 检查角色化行为，非真实引擎任务完成率。 | **实查**[作者代码](https://github.com/KomeijiForce/Codified_Finite_State_Machine)包括 README、LICENSE 和编译脚本 codify_cfsm.py；完整概率转移/推理环境与判别器依赖未核为单一可运行包。Baseline：文本 profile、Codified Profile、PromptTrans、Character Updating、Plot Summary；须保持同 RP LLM/条件判别器。 |
| **H02 RMTBench** · [EMNLP 2025 Findings](https://aclanthology.org/2025.findings-emnlp.730/) | 80 角色、8,156 条用户话语，含人物询问、保持、用户目的、偏好与敏感试探；被测 NPC 自己续写前轮回应，但用户后续话语预先给定。不是玩家实时根据 NPC 发言滚动生成的双向交互。 | **实查数据页** [xiangh/RMTBENCH](https://huggingface.co/datasets/xiangh/RMTBENCH)；作者提供 Claude 3.5 论文原版及 Claude 4.5 扩展版，包含中英文件。访问有需同意条款，README 出现非商业限制而标签显示 Apache-2.0；按各项条款独立理解，不把可浏览页面当已取得授权文件。 |
| **H03 PsyMem** · [TACL 2026](https://aclanthology.org/2026.tacl-1.24/) | 26 个心理指标和显式记忆对齐训练；论文报告 5,414 角色、38,962 段小说对话和 Qwen2.5-7B。测角色心理与记忆响应，而非玩家因果关系或引擎执行。 | 本轮确认 TACL 正式论文与方法/规模；独立的完整训练 JSON、权重和脚本未全部核验，按**待核**而非“缺失”记录。Baseline 应为同人物信息条件下的 profile、记忆输入与对齐训练消融。 |
| **H04 NCP-Bench** · [ICML 2026](https://proceedings.mlr.press/v306/ma26ap.html) | 100 个电影叙事世界、1,660 个初始事实、1,222 条承诺、1,511 个剧情节点。模拟玩家干扰 narrator，评审事实和承诺冲突；目标是叙述者而非单个角色的错误信念，且部分冲突由模型 auditor 判断。 | **实查**[NLP2CT/NCP-Bench](https://github.com/NLP2CT/NCP-Bench) 有完整 YAML 场景目录、运行器、固定 prompt、Baseline 和 HiAgent 方法、单测。等价复现须固定 narrator、玩家模拟器、auditor 模型及生成设置；不能把故事审计结果当引擎事务成功率。 |
| **H05 MCPDial** · [arXiv 2024](https://arxiv.org/abs/2410.21627) | 带玩家与 NPC 两侧 persona 的长对话及穿插函数调用，适合作为对话/工具接口数据而不是完整环境。论文主要做数据构造和定性检查，尚非通用角色表现权威 benchmark。 | **实查**[仓库](https://github.com/salavi/MCPDial-A-Minecraft-Persona-driven-Dialogue-Dataset) 有 train-conversations、test-conversations、测试提示 CSV 与多个实际 JSON；工具标注没有世界状态回执。 |
| **H06 GRAIL / Bayesian Social Deduction** · [ACL 2026 Main](https://aclanthology.org/2026.acl-long.1497/) | Avalon 中将隐藏身份后验的概率推断与语言发言分离；真人受控对局报告 67% 胜率。Agent 只扮演 **Good** 阵营，因此适用于信念跟踪而非反派角色持久欺骗的直接 benchmark。 | **实查**[项目仓库](https://github.com/camp-lab-purdue/bayesian-social-deduction)有站点源文件、项目页面和静态资源；完整数据、模型 checkpoint 和本地 game runner 的逐个文件级检查未完成。评价需区分身份预测精度、胜率、表述自然性和人物身份坚持。 |
| **H07 Fake Player / Distill Bench** · [匿名 ICLR 2026 投稿稿](https://openreview.net/pdf/2e26df077644bbbe3df13f485ea6433e09764b7b.pdf) | 内心独白、动态意图栈、受输入约束的 player message 生成；提出训练数据评估。论文仍是未核实正式录用的投稿稿，模拟输入未经过独立真人分布验证。 | 未确认可以独立复用的训练数据、Distill Bench 和完整代码；按**论文/投稿材料**而非已开放 baseline 记录。 |
| **H08 Quest of Aivengarde** · [FDG 2026](https://portal.findresearcher.sdu.dk/en/publications/quest-of-aivengarde-comparative-study-of-player-experience-across/) | 一套 RPG 比较脚本对白、改写、混合、自由生成，64 人体验/日志补充主观参与感、玩家能动性与自然性。和人格忠实 NLI 不是同一分数。 | 本轮只核到已接收发表记录和摘要，尚未全文阅读或确认环境和行为日志开放；按**元数据／待核**，不写成现成自动评测包。 |
| **H09 Sony CPDC 2025 官方挑战** · [Task 1](https://www.aicrowd.com/challenges/commonsense-persona-grounded-dialogue-challenge-2025/problems/task-oriented-dialogue-task-1) | NPC 在世界观、人物设定、角色知识、玩家基本信息和函数定义下生成语言与函数调用；意图属于玩家侧但不会完整公开给 NPC。动作函数没有执行返回，评分为调用/参数和回复质量。 | **实查**[starter kit](https://github.com/Augustus2011/sony-cpdc-2025-starter-kit) 含函数调用、NPC 数据接口、baseline、SFT/RL 示例与训练/运行脚本；组织方保密最终测试集。不能将公开训练数据指标写成官方隐藏集分数。 |

**工业工程参考（不算第 85 个资源，也不算第 91 篇论文）**：[KRAFTON / NVIDIA 关于 PUBG Ally 的访谈（2026）](https://developer.nvidia.com/blog/how-krafton-built-pubg-ally-a-co-playable-character-powered-by-nvidia-ace/) 介绍世界观察工具、事件驱动的语言模型、行为树 tick 级执行与跨局玩家偏好记忆。该资料主要展示可实施的异步接口，不能替代人物角色一致性实验。

仓库发布状态是**时间点快照**：旧条目如 RoleMemo、DynSess、HAMLET、Video2Roleplay 的部分资源状态均指此前核查时实际文件，不构成永久不可用的判断。做跨文献比较还必须保留数据版本、模型/评分器版本、角色 split 与可见信息条件。
