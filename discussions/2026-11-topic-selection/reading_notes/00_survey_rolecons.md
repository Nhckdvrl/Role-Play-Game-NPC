# Role Consistency in RPAs: A Survey (EMNLP 2026 Findings) — full read
- Frame: role consistency = longitudinal maintenance of an evolving role state (identity, knowledge boundaries, style, memory/relations, values, behavioral logic, safety boundaries); "from profile to state", then "constrained agency".
- Taxonomy: memory&retrieval (role-state memory, retrieval grounding, memory control); role-aware reasoning (standpoint, affective, decision, self-judgment); training/alignment (supervised consistency, contrastive/preference, reward-based, boundary-aware).
- Benchmark card over 6 dims K/E/P/M/R/B. Claim: benchmarks strongest on K (knowledge) and E (expression/style); sparse on M (memory/temporal continuity) and B (robustness to drift/boundary pressure). "Many consequential RPA failures are longitudinal or conflict-driven rather than single-turn factual errors."
- Evaluation advice: combine automatic checks, human judgment, calibrated judges with controls for verbosity, familiarity, and helpfulness-vs-fidelity confusion.
- Open challenges (Sec 6):
  1. controllable long-term memory: typed memory items (source, scope, confidence, temporal validity, access boundary); tests for delayed correction, selective forgetting, conflicting evidence;
  2. robust evaluation under role attacks: false assertions, break-character requests, scenario shifts, memory manipulation; branching trajectories with matched clean/attacked runs; time-to-first-drift, recovery, persistent corruption; refusal without leaving character; defense collapsing into generic safety voice;
  3. language-grounded multimodal/agentic consistency: cross-modal state binding; "grounded role decision" as unit; counterfactual scene edits;
  4. conflict-aware role-state arbitration: precedence among canon, interaction memory, user goals, policy, safety; paired conflicts (canon vs user assertion, loyalty vs evidence, role goal vs safety); stability over later turns.
- Figure 6: share of papers covering B (robustness) rose to 57% in 2026; R (reasoning) 46%.
- My read: survey is short (6pp), mostly taxonomic; value = the gap claim (M, B under-measured) and the attack/arbitration agenda. Note overlap of challenge 2 with our archived persona-consistency study (false assertions, judge problems) and challenge 4 with reason-sensitive-roleplay (evidence vs loyalty).
