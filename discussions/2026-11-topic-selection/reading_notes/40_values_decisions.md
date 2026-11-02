# Values / decisions line
## Too Good to be Bad (ACL 2026 Findings, 2511.04962)
- Moral RolePlay benchmark, 4-level moral scale; fidelity declines monotonically as morality decreases (3.21 paragons -> 2.62 villains); biggest drop at flawed-good -> egoist boundary; worst traits: Deceitful, Manipulative (replaced by superficial aggression); Arena ability poor predictor; highly safety-aligned models worst. Judge-based scores.
## RoleCDE (ACL 2026 Findings, 2606.01552)
- ~8k profiles, ~24k two-option dilemmas (role value vs alignment constraint), 3 difficulty levels, 8 role categories. "Role–Value Decoupling": models systematically default to alignment/morality-consistent decisions even with explicit role conditioning; invariant to difficulty, varies by role category. Attributed to dominance of alignment-oriented priors. CoT gives limited/unstable gains; RoleCDE fine-tuning (SFT/DPO) mitigates with some general-metric losses (per ROADMAP).
