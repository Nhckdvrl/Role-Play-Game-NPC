# 本专项：方法依据与增量文献

> 核查日期：2026-11-01。此页补充当前研究直接需要的来源，不改动2026-10-30主索引的113篇／107项历史统计。原论文结论限于原协议；本项目未独立复现下列结果。本轮补核以官方页面、摘要和已有方法阅读为基础，不宣称重新精读完整领域。

## 1. 教师脚手架内化

**OSPD: On-Policy Self-Distillation for Persona-Consistent Dialogue**，EMNLP 2026 Main，原索引RP-044。官方：[论文页面](https://aclanthology.org/2026.emnlp-main.2105/)。

完整人设教师与简短人设学生在学生轨迹上进行自蒸馏，使用角色相关的散度选择与属性遮蔽。对本项目的意义：部署时减少显式脚手架可以是训练目标，不因强提示有效就停止后训练。区别：我们重点是历史与当前有效条件的使用；必须保证学生拥有足够的人物事实，不用教师独有秘密制造不可识别任务。

**You Changed Your Mind, The Model Didn't: Demystifying Intent in Multi-Turn Dialogue**，Intent-OPSD，arXiv:2610.06496，2026-10-05预印本。官方：[arXiv](https://arxiv.org/abs/2610.06496)。

以有效意图信息指导教师，将对包含旧要求的完整对话的处理训练给学生。对本项目的意义是“生效条件摘要→自然长历史”的教师／学生不对称。区别：NPC有自身目标，不是用户最新要求自动拥有最高优先级，不能直接把“服从最后要求”当人物一致性。

## 2. 历史惯性与跨提示关系

**Mitigating Conversational Inertia in Multi-Turn Agents**，ICML 2026。官方：[PMLR](https://proceedings.mlr.press/v306/wan26a.html)。

研究多轮agent对自身历史回复的自模仿与惯性，并以长短上下文偏好构造进行缓解。它提供现象和训练参照，不证明本项目模型已存在同样机制。我们需要在当前相关条件匹配时同时考察不当配合与不当拒绝，并回到自然角色对话。

**CPC-GRPO: Answer-Free Reinforcement Learning with Cross-Prompt Consensus Rewards**，ACL 2026 Findings。官方：[ACL Anthology](https://aclanthology.org/2026.findings-acl.1486/)。

利用同意图的提示变体、跨提示候选重评分与联合更新。对本项目的启发是可利用跨输入的结构，不必把节点全部拆散。区别：我们既有应保持的边，也有条件改变后应不同的边；节点决定与依据合格是关系奖励的锚点，不能只奖励答案共识。

## 3. 信用分配与优化

**Counterfactual Multi-Agent Policy Gradients**，COMA，AAAI 2018；arXiv:1705.08926。官方：[AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/11794) · [arXiv](https://arxiv.org/abs/1705.08926)。

提供固定其他行为、边缘化当前行为的反事实信用分配思想。我们的分支是不同输入上的角色回复，并非直接照搬多agent环境；通过可分解的节点和边因子计算条件分数，不训练COMA的centralized critic。

**Back to Basics: Revisiting REINFORCE Style Optimization for Learning from Human Feedback in LLMs**，ACL 2024，RLOO；arXiv:2402.14740。官方：[ACL Anthology](https://aclanthology.org/2024.acl-long.662/) · [arXiv](https://arxiv.org/abs/2402.14740)。

提供同一输入下独立样本的leave-one-out基线与REINFORCE式LLM优化参照。本项目同节点其他样本作为基线，不把六个不同条件直接当同一prompt的标准GRPO组；固定评分函数与policy版本是推导起点。

**Direct Preference Optimization: Your Language Model is Secretly a Reward Model**，NeurIPS 2023；arXiv:2305.18290。官方：[arXiv](https://arxiv.org/abs/2305.18290)。

DPO是同条件下偏好学习的强参照，可以通过数据中的条件差异学习不同选择。我们的论点不是DPO不能学习条件，而是显式族关系是否带来可测的效率、薄弱分支或泛化收益。

## 4. 已有领域资产如何接续

以下按原索引引用，不在本页重复宣称资源已经完整复现：RP-013 CoSER、RP-021 RoleMRC、RP-025 HER、RP-039 CRPO、RP-040 MOA、RP-061 Persistent Personas、RP-080 RoleCDE、RP-087 CharacterBench。论文与实际数据／模型状态见[LITERATURE](../../../docs/LITERATURE.md)和[RESOURCE_ATLAS](../../../docs/RESOURCE_ATLAS.md)。

原索引中的角色奖励、思考、人格探针和多轮基线是实现工具箱。先选与当前问题最直接、能够在本地跑通的资产；不要求把每篇都复现，也不将不同judge、底座或输入信息下的分数直接拼为同一排名。

## 5. 本项目自己的方法与证据

对称度数边权、节点锚定的保持／改变核、可选固定锚点目标与独立教师恢复是本项目当前可测试设计，数学定义见[METHOD](METHOD.md)。已有论文支持相关技术路线，不替我们证明该组合有效。

16项代码测试检验实现与玩具梯度；真实模型失效、评分器准确性、生成数据质量、训练收益和推理成本需要各自的实验记录。正式投稿前重新冻结并核验实际使用的论文版本、代码commit、数据许可和评测协议。
