# Evaluation / what-models-contribute line

## ANIMASK (2609.16667, Sep 2026) — key paper
- Freeze 40 books/scripts into story worlds; characters act on their own motivations; replay from freeze point with 6 actor models (GPT-5.5, Claude Sonnet 5, Gemini 3.7 Flash, DeepSeek-V4-Flash, Kimi K2.6, Qwen3.7-Plus); author continuation as human reference.
- RQ1: replays converge away from canon in ONE shared direction: flatter, cooler, tensions unresolved; only 7/240 replays end with a goal achieved; typical ending = standstill (keep goals, avoid irreversible moves, wait). Directional test: sign agreement across stories + paired permutation, Holm-corrected.
- RQ2: personas stay present (in-story interviews, facet means 87–96/100, median drift 0).
- RQ3: 3,846 decision points, action-strength scale yield<hold<press<oppose<cross; compare persona action with no-persona action. 3/4 of choices: model default already inside persona-implied set ("adhere-but-empty"); where they diverge the MODEL is the cautious one, holding where persona would press.
- Formal model: π_M(a|c,h) ∝ q_c(a|h)·w_M(a|h): persona call × model weight; if w_M(a)=0 the action never happens however strongly the card calls for it.
- Slogan: "The persona guarantees who the character is, and the model sets how far the character will go."
- Judges used for decision listing / implied sets (LLM). Code public.
- Implication: fidelity benchmarks that check identity (interviews, knowledge) miss this; the failure is in consequential agency, model-driven, consistent across 6 frontier models (robust!).
## Anonymous Benchmarking (SIGDIAL 2026, 2603.03915)
- Anonymizing famous character names significantly lowers scores on CharacterEval/RoleAgentBench -> benchmarks partly measure recognition/memory; adding personality info (MBTI/BFI, even self-generated) consistently helps.
