# Latent multi-hop reasoning (read 2026-11-11, motivated by S1: experience -> attitude -> decision is a two-hop inference)

## Biran, Gottesman, Yang, Geva, Globerson — Hopping Too Late (EMNLP 2024, 2406.12775)
- 82k Wikidata two-hop queries ("the spouse of the performer of Imagine is"); filtered for shortcuts; correct vs incorrect cases where both single hops are known.
- Patchscopes: bridge entity resolved early at the end of the first hop (t1), then propagates to the last token; the second hop is resolved at the last token only in *later* layers. In failures, the bridge appears later and the target less often.
- **Back-patching**: patch a later-layer hidden state at the last token back into an earlier layer; up to 66% of incorrect cases become correct for some (source, target) layer pair → later layers may lack the functionality to run the second hop ("hopping too late").
- For us: experience → attitude is a first hop computed in context; attitude → choice is the second. S1 probes show the experience-derived attitude reaches the decision token at the same layer band as a stated attitude (Mistral L20) but at ~0.6–0.75 strength, so "too late" is not obviously the story; back-patching is still a cheap, discriminating test.

## Yang, Gribovskaya, Kassner, Geva, Riedel — Do LLMs Latently Perform Multi-Hop Reasoning? (ACL 2024, 2402.16837)
- Measures first-hop (internal recall of the bridge entity increases when the prompt refers to it) and second-hop (does more recall make the answer more consistent with the bridge's attribute). Strong first-hop evidence for some relation types (>80%), highly context-dependent; first hop scales with size, second hop does not (≈0.6 at 7B/13B/70B).
- For us: the analogue of "second hop does not scale" would be: inferring the attitude (K) improves with scale, applying it (decision) does not. Testable cheaply with Qwen3 sizes (0.6B–32B are cached).

## Balesni et al. — Lessons from Studying Two-Hop Latent Reasoning (2411.16353)
- Fine-tuned synthetic facts: models recall each fact perfectly but compose two separately learned facts at chance without CoT; forcing storage order or encouraging the first hop does not fix it. Composition succeeds when facts co-occur in a document, in context, or when one fact is natural.
- For us: in-context composition is the easy regime, and our models do compose partially (decision effect > 0). The gap is quantitative, not total.

# Related to the M2 access-gating method (searched 2026-11-12, abstracts only)
- Information-flow control for LLM agents works at the tool or agent layer, outside the model: APPA (2607.24625), FLOWSEAL (2609.14003; leakage driven by model "confusion", tool-level interceptor with a provenance lattice), MNC (2608.01719). The survey "Agents That Know Too Much" (2606.26627) argues IFC best matches compositional, intermediate-step leakage.
- Inside-model privacy control: "Personalized Privacy Control via Attention Head Intervention" (2608.21209), framed by contextual integrity. GIF: geometric IFC for LLMs (2606.23277).
- System-prompt drift: Li et al. 2024 (2402.10962), attention decay to the system prompt; split-softmax boosts attention to it. Persona placement effects: system vs user prompt (2601.18572, 2601.20757).
- Our M2 differs in three ways: (a) the labels come from the model's own access judgement (K-type ability); (b) masking is restricted to the mid-layer window the knockouts identified; (c) the target is role-play epistemic access (who could know what), not user privacy. To check before claiming novelty: whether 2608.21209 or 2606.23277 already mask attention by span labels.

# Provenance and role confusion (read 2026-11-12)

## Prompt Injection as Role Confusion (2603.12277, ICML 2026)
- Claim: LLMs perceive the source of text ("who is speaking") from how it SOUNDS, not from its role tag. Injected text inside a <tool> span that sounds like <user> text occupies the same latent region as real user text. Role probes trained on real tags show this. "CoT Forgery" (fabricated reasoning in user or tool text) is mistaken for the model's own thoughts. Role confusion predicts attack success before generation. Position determines "Systemness" the way style determines other roles, which explains why long system prompts lose priority.
- For us: a direct analogue. Our provenance markers (which character's card a memory sits in, "nobody in Ashford has heard of these") do not survive into the decision computation, and the decision reads content. Their position→Systemness finding parallels our location effect (situation region > profile region).
- Method to borrow: probes for "whose information is this" at the content tokens of a memory (M4), with family-held-out folds.

## ConfAIde: Can LLMs keep a secret? (Mireshghallah et al., 2310.17884)
- Contextual-integrity benchmark in tiers. Models disclose private information in contexts where humans would not, even when they can state the norm. A knowing-vs-doing gap in privacy, with the same shape as our access leak.
