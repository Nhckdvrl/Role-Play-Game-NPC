# Training / reward line — close-read notes

## HER (ACL 2026 Findings, 2601.21459)
- Dual-layer thinking (hidden 3rd-person system thinking + visible 1st-person role thinking), data via 3-stage reverse synthesis on CoSER; principle-aligned generative RM (GRM) + RL.
- Gains: +30.26% CoSER, +14.97% MiniMax RP bench vs Qwen3-32B.
- Explicitly names: open-ended RP outputs non-verifiable -> RM/PO prone to bias & shortcut learning; LLM judges biased.
- Reward hacking observed in their GRM: position, length, and "pattern bias" (multi-dim comparisons collapse to all-A/all-B). Collapsed setting: top-1 pattern share >90% by step 28, 96.3% at step 50 (entropy 1.32->0.29); diversified data keeps 43–54%.
- Policy-side: training collapses into a single response structure (thought/action/speech interleaving) unless SFT data is diversified.
## Character-R1 (2601.04611)
- RLVR for role-aware reasoning: cognitive-focus reward (tag+attribute exact/semantic match over 10 "elements"), reference-guided reward (overlap with reference), character-conditioned reward normalization (reward distributions differ across characters/reward types; naive sums let some dominate).
- Eval: CharacterBench, SocialBench (judge-based). Limitation admitted: rule/semantic matching can't capture psychological nuance.
## RAIDEN-R1 / VeriRole (2505.10218 early version)
- Verifiable role-awareness reward from mined role-specific keywords; 14B-GRPO 88% on script knowledge / conversation memory (RAIDEN).
- Notes: LLM-as-reward "subjective bias"; Qwen2.5-7B unstable under GRPO; SFT on CoT data does not help.
- Rewards are knowledge/memory keyword hits -> narrow slice of fidelity.
## CRPO (ICML 2026, 2605.25511)
- Claims GRPO-style RL on RP causes loss of character fidelity / "style collapse": intra-group normalization rewards logically correct but de-characterized generic responses; static KL constraints hurt complex (high-entropy) characters and cause forgetting for simple ones; no negative contrast against the generic mode -> policy stays in "safe but boring center".
- Fixes: dual-stream advantage (task vs style), character-entropy-aware adaptive constraints, generic responses as contrastive negative anchors (1 anchor helps, more doesn't).
- Code public (github Toyhom/CRPO). Evaluation judge-based + small human eval.
## MOA (ACL 2026, 2512.09756)
- Multi-objective RL over fine-grained rubrics (LLM-as-judge per rubric), dynamic weighting by trend/gradient; thought-augmented rollouts + off-policy guidance.
- Vanilla GRPO from SFT checkpoint performs poorly even at t=1.5 (exploration collapse). Eval PersonaGym, RoleMRC (judge-based). Limitation: judge cost; self-scoring unexplored.
## CPO (EMNLP 2025 Findings, 2508.09074)
- Group-wise comparative scoring instead of sample-wise scalar rewards; CharacterArena = simulate multi-turn trajectories then trajectory-level comparison (to avoid context bias from non-self-generated histories).
- Length reward hacking -> soft overlength penalty. Human-eval win rate "more conservative" than CharacterArena (auto vs human gap). Chinese; single-turn optimization only.
## DynSess (EMNLP 2026 Findings, 2605.29256)
- RP is session-level; turn-level eval on fixed (not self-co-produced) history cannot see drift/repetitive loops. DynSess-Eval: user simulator (Doubao-1.5-pro-character) + Gemini-3-Flash rubric judge over 10-turn sessions; criteria target gradual persona drift, repetitive loops, memory use.
- Training: multi-turn lookahead search -> DSPO (segment DPO, off-policy), GSRPO (session-group, on-policy). 32B matches a 200B proprietary model in blind human eval.
- Admitted: single judge; residual auto–human discrepancies; Likert central tendency (top-model margins 0.05–0.15); self-preference bias; case: turn-level judge rates early turns highly while the model later degrades into templated evasive/user-mirroring tone.
## LSH-RL (EMNLP 2026 Findings)
- Motivation (key): SFT, DPO and coarse episode-level RL "over-reinforce safe stylized responses that appear in-character but are repetitive, low-information, or weakly grounded in the evolving scene".
- Multi-role self-play; short-horizon utterance/action rewards + long-horizon trajectory reward; gate trajectory credit through locally qualified turns (coarse episode reward gives weak turns undeserved credit). PersonaArena/CharacterBox; judges Qwen3-32B and GPT-4o-mini; moderate human IAA. Limit: judge biases/prompt sensitivity inherited.
## OSPD (EMNLP 2026 Main, 2609.34418)
- On-policy self-distillation: same model as teacher with full profile, student with brief summary; student rolls out its own trajectories (removes exposure bias: "a single OOC reply corrupts all subsequent context").
- Finding: teacher confidence bimodal (peaked at character-critical tokens, diffuse at generic) -> role-aware divergence switching (forward/reverse KL by entropy); progressive trait masking: identity/personality transfer easily from brief summaries; knowledge and history are hardest.
- Drift curve (P2L, judge-based): 10->60 turns: SFT 82->60 (−22), multi-turn RL 86->74, OSPD 88.2->83.0.
- Limits: scale dependence (<7B can't use detailed profile; large models may already internalize), LLM trajectory filter bias.
## RoleRMBench/RoleRM (2512.10575)
- 7 capability categories; general RMs degrade on RP, narrative cluster (introduction/progression/stitching) worst (<65%). RoleRM (8B) +24% over open/closed RMs. Pair constructions NEB/BW/FULL; mixed with general preference data. Bench small (1 pos/1 neg per dialogue).
## RAR / Thinking in Character (NeurIPS 2025, 2506.01748)
- LRM thinking in RP suffers attention diversion (forgets role) and style drift (formal, rigid reasoning). Role Identity Activation (profile-guided reasoning) + Reasoning Style Optimization (distill style-appropriate traces). CharacterBench/SocialBench (judge). Distill+MoreThink: longer traces reduce coherence.
## Reasoning Does Not Necessarily Improve RP (ACL 2025 Findings, 2502.16940)
- 6 benchmarks × 24 LLMs × {direct, CoT, reasoning-LLM}: CoT may hurt (attention diversion, linguistic style drift); reasoning-distilled models worse than originals; scaling law weak/inconsistent; CoT helps on InCharacter and RoleBench only. Proposes role-aware CoT and RL as future work.
## R4 (ICLR 2026) — PDF not retrievable (OpenReview HTML); rely on ROADMAP 7.10 ablation numbers.
