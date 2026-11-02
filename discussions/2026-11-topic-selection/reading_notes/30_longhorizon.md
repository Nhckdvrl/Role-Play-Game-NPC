# Long-horizon / drift line

## Persistent Personas? (EACL 2026, 2512.12775)
- Protocol: >100-round persona dialogues (persona-directed vs goal-oriented with PRISM real user queries) then dialogue-conditioned benchmarks; 7 SOTA models.
- Fidelity degrades, faster in goal-oriented dialogues (task instructions pull away); models revert to default/no-persona behavior: final-round persona-vs-baseline extracted token patterns −41.27% (CI 36.5–45.7%).
- Fidelity–instruction-following trade-off: no-persona baselines initially beat persona models; gap shrinks as fidelity fades. Excessive safety rises in persona-directed dialogues. Scale narrows but doesn't eliminate gaps (incl. Gemini-2.5-flash). Mixed-effect regressions; bootstrapped CIs.
## Attractor States in Multi-Turn LLM Conversations (2606.30571)
- 20-turn LLM–LLM debates; self-play endpoints = reproducible model-specific attractor basins in embedding space; mixed-play: asymmetric pull (Claude Haiku resistant & attracting partners toward meta-commentary; GPT-4o-mini malleable). Not reducible to stance convergence. Frames persona drift as convergence "to a mode most reinforced in the training signal" (assistant persona underspecified; Nostalgebraist 2025; Lu et al. 2026 Assistant Axis).
## The Assistant Axis (2601.10387)
- PC1 of persona (archetype) activation space = "Assistant Axis" across several models; also present in pre-trained models (promotes consultant/coach archetypes). Steering away -> identifies as other entities, theatrical/mystical style. Deviation along axis predicts persona drift (meta-reflection, emotionally vulnerable users). Activation capping stabilizes, also against persona jailbreaks. "Post-training steers models toward a region of persona space but only loosely tethers them."
## Prompting Against Persona Drift (2609.24532)
- Student (ADHD) persona simulation, 1,200 × 28-turn conversations, 4 LLMs; LLM-rated drift. Reinjection −35–38%, reflective reminder −22–27%, monitor-generated behavior-specific instruction −87%; none eliminates drift; adaptive timing no better than static.
## Dynamic Persona Coherence (ACL 2026, 2026.acl-long.1336)
- Static persona conflates identity consistency with emotional rigidity -> robotic repetition or catastrophic drift. L/M/S psychological state (long identity, mid meaning/stress, short affect) + critic/case-repo/drift-suppressor loop on GPT-4o/Claude-3.5/DeepSeek-V3.2 (+16–84% critic score; evaluator-repairer co-designed).
## Consistently Simulating Human Personas w/ Multi-Turn RL (NeurIPS 2025, 2511.00222)
- User-simulator personas (patient, student, chat partner); metrics prompt-to-line, line-to-line, Q&A consistency, validated vs human annotation; multi-turn PPO with these as rewards cuts inconsistency >55%. Caution (ROADMAP): static consistency can punish legitimate change.
## REMP (EMNLP 2026 Findings)
- 160 characters, 80 trajectories × ~60 sessions × ~800 turns (prebuilt history), probe events for persona/emotion/memory/relationship; anchor-based eval; 11 LLMs: memory integrity and emotional consistency are main bottlenecks; memory decays with distance. Only 4 trajectories public.
## MRBench / MRPrompt (ACL 2026 Findings, 2603.19313)
- Memory-driven RP: Anchoring, Recalling, Bounding, Enacting; persona facets averaged into generic replies without cues; benchmarks with explicit scene descriptions inflate success. MRPrompt lets Qwen3-8B match Qwen3-Max/GLM-4.7; upstream memory gains propagate downstream.
## StratMem-Bench (ACL 2026, 2604.26243)
- 657 instances; memory pools of required / supportive / irrelevant memories; models separate required vs irrelevant well but struggle when supportive memories are in play (judge + rule aggregation).
