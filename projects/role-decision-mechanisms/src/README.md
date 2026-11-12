# src 索引

按用途分组；说明取自各脚本的文档字符串第一行。实验与脚本的对应见 [../EXPERIMENTS_LOG.md](../EXPERIMENTS_LOG.md)。

## 场景族与数据

| 文件 | 说明 |
| --- | --- |
| [families.py](families.py) | Scene families for slice 1: experience -> belief/preference -> decision. |
| [families_identity.py](families_identity.py) | Identity slice: a CATEGORY cue (occupation; implies a preference only through world knowledge) vs an INDIVIDUATING |
| [families_prec.py](families_prec.py) | Precedent-style experiences for the slice-1 families: a past CHOICE of the same kind as the decision, |
| [families_test.py](families_test.py) | HELD-OUT TEST families (T set). Written after all dev experiments; never used for tuning. |
| [families_v2.py](families_v2.py) | v2 scenes: convenience is counterbalanced against the attitude pole. |
| [families_values.py](families_values.py) | Slice 2: value priorities -> decision. Same structure as families.py. |
| [families_values_test.py](families_values_test.py) | HELD-OUT value families (VT set): 12 value pairs NOT used in the dev value slice (families_values.py), modern settings. |

## 提示构造

| 文件 | 说明 |
| --- | --- |
| [build_capab.py](build_capab.py) | Side-effect check for the role-decision SFT: general multiple-choice knowledge (MMLU 1000 test items, ARC-Challenge |
| [build_freegen.py](build_freegen.py) | Measurement validity: free-form in-character replies on the T set (card format), classified into options. |
| [build_identity.py](build_identity.py) | Identity slice: occupation (category cue) vs own experience (individuating cue) -> K / P / EU decisions. |
| [build_identity_methods.py](build_identity_methods.py) | Frozen self-bridge (three-way K first; dev-frozen wording, unchanged) on the identity slice. Decisions only. |
| [build_lc_inject.py](build_lc_inject.py) | Natural-context counterfactual injection (LifeChoice stories as realistic long context; design fixed before running). |
| [build_lc_inject_k.py](build_lc_inject_k.py) | K counterpart of the natural-context injection (E3): same 400 stories, same injected sentences and positions. |
| [build_lifechoice.py](build_lifechoice.py) | External validity on natural text: LifeChoice (Xu et al. 2024/2025; character decisions from novels, expert-written |
| [build_lifechoice_kfirst.py](build_lifechoice_kfirst.py) | LifeChoice K-first (natural-text analogue of the self-bridge; designed once, not tuned). |
| [build_s1.py](build_s1.py) | Build slice-1 prompts: experience -> belief/preference -> decision. |
| [build_s10.py](build_s10.py) | S10: slice-1 v2 scenes WITHOUT any cost sentence (no competing practical factor), plus the two cost |
| [build_s11.py](build_s11.py) | S11: legitimate vs illegitimate access to another character's experience. |
| [build_s12.py](build_s12.py) | S12: is the 'profile region' penalty (S4) really dilution by other sheet content? |
| [build_s2.py](build_s2.py) | Build S1 v2 prompts. |
| [build_s3.py](build_s3.py) | S1 v3: prompt interventions on the v2 scenes (cost arrangements and option orders kept). |
| [build_s4.py](build_s4.py) | S4: why does the 'bridge' (attitude Q&A right before the decision) work so well? |
| [build_s5.py](build_s5.py) | S5: self-bridging. Insert the MODEL'S OWN answer to the Knowing question right before the decision. |
| [build_s6.py](build_s6.py) | S6: self-bridging with a three-way Knowing question. |
| [build_s7.py](build_s7.py) | S7: does the retrieval KEY decide whose experience counts? |
| [build_s8.py](build_s8.py) | S8 (slice 2): value priorities -> decision, in the slice-1 format. |
| [build_s9.py](build_s9.py) | S9: event-style vs precedent-style experiences (slice-1 families, v2 scenes with cost counterbalance). |
| [build_sft.py](build_sft.py) | SFT data from DEV families only (slice-1 v2 prompts incl. told; values slice). Decisions only (P, EU). |
| [build_test.py](build_test.py) | Build the HELD-OUT test set (T set) from families_test.py in three context formats. |
| [build_test_conflict.py](build_test_conflict.py) | T-conflict: the role's OWN experience and INACCESSIBLE evidence point in OPPOSITE directions (held-out T families). |
| [build_test_dlg.py](build_test_dlg.py) | T-dlg: the held-out T families rendered as DIALOGUE / story history instead of character sheets. |
| [build_test_methods.py](build_test_methods.py) | Frozen dev methods on the T set (decisions only, P and EU, wording 0/1, both costs and orders). |
| [build_values_test.py](build_values_test.py) | VT: held-out value slice (12 new value pairs, families_values_test.py) in the T formats (card / json / prose). |

## 打分、生成与训练

| 文件 | 说明 |
| --- | --- |
| [gen_vllm.py](gen_vllm.py) | Greedy generation for chat prompts. usage: gen_vllm.py MODEL TAG IN.jsonl OUT.jsonl [max_tokens] |
| [score_ab.py](score_ab.py) | Next-token A/B log-probs for chat prompts with arbitrary message lists (vLLM, greedy, 1 token). |
| [score_abc.py](score_abc.py) | Next-token A/B log-probs for chat prompts with arbitrary message lists (vLLM, greedy, 1 token). |
| [score_abcd.py](score_abcd.py) | Next-token A/B log-probs for chat prompts with arbitrary message lists (vLLM, greedy, 1 token). |
| [think_analyze.py](think_analyze.py) | Thinking ON vs OFF (Qwen3), EU wording 0. sens = P(pos)\|pos - P(pos)\|neg, from final answers (think) or A/B probs (no think). |
| [think_vllm.py](think_vllm.py) | Qwen3 with thinking ON: generate, then read the final A/B answer after </think>. |
| [train_sft.py](train_sft.py) | LoRA SFT on DEV decision data (build_sft.py output). Loss on the assistant answer letter only. |

## 机制实验

| 文件 | 说明 |
| --- | --- |
| [mech_backpatch.py](mech_backpatch.py) | Back-patching the character sheet: give the decision access to later-layer (ownership-bound) sheet representations. |
| [mech_backpatch_analyze.py](mech_backpatch_analyze.py) | Back-patching: decision sens per condition for each SRC>TGT pair. usage: mech_backpatch_analyze.py BP.jsonl |
| [mech_collect.py](mech_collect.py) | Collect final-token residual streams (all layers) and the A/B logit difference. |
| [mech_common.py](mech_common.py) | Shared helpers for the mechanism experiments (plain transformers + PyTorch hooks). |
| [mech_dla.py](mech_dla.py) | Direct logit attribution at the final position, per layer and component (attention / MLP). |
| [mech_dla_analyze.py](mech_dla_analyze.py) | Analyse mech_dla.py: per-layer direct logit attribution of (pos - neg valence), attention vs MLP, |
| [mech_gate.py](mech_gate.py) | Model-guided access gating. |
| [mech_gate_analyze.py](mech_gate_analyze.py) | Summarise mech_gate.py: judge accuracy and decision sens under each gating variant. |
| [mech_gate_test.py](mech_gate_test.py) | Model-guided access gating. |
| [mech_identity_knock.py](mech_identity_knock.py) | Identity slice, attention knockout: how much do K and the decision draw on the OCCUPATION vs the role's own |
| [mech_identity_knock_analyze.py](mech_identity_knock_analyze.py) | Summarize mech_identity_knock output: effect (LD(pos) - LD(neg), logits) per mode x form, base and after |
| [mech_knockout.py](mech_knockout.py) | Attention knockout: does the decision read the source sentence's conclusion (its last token) or its content? |
| [mech_knockout_analyze.py](mech_knockout_analyze.py) | Summarise mech_knockout.py: decision sens (LD pos - LD neg) after blocking tail->source attention. |
| [mech_lc_knock.py](mech_lc_knock.py) | Natural-context mechanism check: does the effect of an injected precedent sentence in a real long story flow through |
| [mech_lc_knock_analyze.py](mech_lc_knock_analyze.py) | Summarise mech_lc_knock: mean P(target) shift relative to the uninjected story, per source, for each knockout variant. |
| [mech_owner.py](mech_owner.py) | Ownership probe: does the representation of a memory's CONTENT encode whose memory it is? |
| [mech_owner_analyze.py](mech_owner_analyze.py) | Ownership probe analysis: train a 'role holds this' direction (self vs other) on half of the families, |
| [mech_owner_analyze2.py](mech_owner_analyze2.py) | Ownership vs position on v1 data (both card orders per family): train 'self vs other' on held-out-family folds with |
| [mech_patch.py](mech_patch.py) | Interchange patching on the decision tail. |
| [mech_patch_analyze.py](mech_patch_analyze.py) | Summarise mech_patch.py output. |
| [mech_probe.py](mech_probe.py) | Linear read-out of the role's attitude at the final (decision) token. |
| [mech_probe_gate.py](mech_probe_gate.py) | Two-pass ownership-probe gating (mechanism-derived method; develop on dev ONLY, then freeze). |
| [mech_qend.py](mech_qend.py) | Is the Knowing answer computed latently when the K question appears inside a decision prompt? |
| [mech_qend_analyze.py](mech_qend_analyze.py) | Analyse mech_qend.py: valence read-out at the end of the K question. |
| [mech_readout.py](mech_readout.py) | Does the same amount of attitude signal at the decision token produce the same logit shift in both forms? |
| [mech_sources.py](mech_sources.py) | Where in the tail is the role information, and why does the experience form carry less? |
| [mech_sources_analyze.py](mech_sources_analyze.py) | Summarise mech_sources.py outputs. |
| [mech_srcsteer.py](mech_srcsteer.py) | Is the weak decision effect of an experience inherited from a weak attitude signal at the experience itself? |
| [mech_srcsteer_analyze.py](mech_srcsteer_analyze.py) | Summarise mech_srcsteer.py: decision sens (LD pos - LD neg) under source steering, per condition. |
| [mech_steer.py](mech_steer.py) | Is the attitude direction causally used by the decision? |
| [mech_steer_analyze.py](mech_steer_analyze.py) | Summarise mech_steer.py. |

## 分析

| 文件 | 说明 |
| --- | --- |
| [analyze_capab.py](analyze_capab.py) | Accuracy on MMLU (1000) and ARC-Challenge (500), base vs role-decision SFT. usage: analyze_capab.py |
| [analyze_conflict.py](analyze_conflict.py) | T-conflict: own experience vs opposite inaccessible (other / world) or legitimately told evidence. |
| [analyze_conflict_additive.py](analyze_conflict_additive.py) | Does a logit-additive model predict the conflict results? |
| [analyze_freegen.py](analyze_freegen.py) | Free-generation validity: classify each sampled reply (two judges, two option orders) into pos / neg / unclear, |
| [analyze_gate_test.py](analyze_gate_test.py) | T-set gating: sens (logit units) by owner/form, overall and per format, for base vs judge-gated. |
| [analyze_identity.py](analyze_identity.py) | Identity slice: weight of occupation (category) vs own experience (individuating) in K and decisions. |
| [analyze_k_dec_consistency.py](analyze_k_dec_consistency.py) | Item-level consistency between K and the decision of the same model on the same context. |
| [analyze_lc_inject.py](analyze_lc_inject.py) | Natural-context injection: shift of P(target option) caused by one injected sentence, by source and position. |
| [analyze_lc_inject_k.py](analyze_lc_inject_k.py) | K for the natural-context injection: P(Yes) to "Does <name> know that someone once chose X ...?" by source/position; |
| [analyze_lifechoice.py](analyze_lifechoice.py) | LifeChoice accuracy: per item, letter probabilities (normalised over A-D) are mapped back to option identity and |
| [analyze_logit_scale.py](analyze_logit_scale.py) | Scale check: role effects in LOGIT units (log p_pos/p_neg), T set. Per family, cost arrangement and mode, |
| [analyze_probe_gate.py](analyze_probe_gate.py) | Sens (logit units) by owner/form, base vs probe-gated; also the mean fraction of context lines gated. |
| [analyze_probe_gate_story.py](analyze_probe_gate_story.py) | Probe gating on real-novel injection stories (E3 set, near position, original order, first 100 items). |
| [analyze_s1.py](analyze_s1.py) | Analyse slice 1. |
| [analyze_s10.py](analyze_s10.py) | S10: attitude effect in decisions with no cost sentence, vs v2 (cost-counterbalanced). |
| [analyze_s12.py](analyze_s12.py) | S12 analysis: attitude effect (P,EU; both costs) per sheet variant x placement x form. |
| [analyze_s2.py](analyze_s2.py) | Analyse S1 v2 (convenience counterbalanced; world-event condition). |
| [analyze_s3.py](analyze_s3.py) | Analyse S1 v3 prompt interventions. |
| [analyze_s8.py](analyze_s8.py) | Analyse S8 (values slice). sens = p_pos(pos) - p_pos(neg), per family, bootstrap CI over families. |
| [analyze_s9.py](analyze_s9.py) | S9: event vs precedent experiences. usage: analyze_s9.py PROMPTS RUN1 [RUN2 ...] |
| [analyze_test.py](analyze_test.py) | Held-out T set: do the dev phenomena replicate on new families, settings and formats? |
| [analyze_test_methods.py](analyze_test_methods.py) | T set, decisions only: plain vs frozen methods (bridge_correct, selfbridge3; optional extra runs). |
| [analyze_values_test.py](analyze_values_test.py) | Held-out value slice (VT): K and decision sens by owner/form, overall and per format; bootstrap CI over 12 families. |
| [heart_analyze.py](heart_analyze.py) | HEART accuracy per condition (argmax over A-D, averaged over the two option rotations; per-question bootstrap CI). |
| [heart_build.py](heart_build.py) | HEART-Bench external validity: does externalising the role's conclusion help memory -> decision, |
| [rp_compare.py](rp_compare.py) | Role-play-trained Llama-3.1-8B variants vs Llama-3.1-8B-Instruct, on dev v2 and the T set. |
| [scale_summary.py](scale_summary.py) | Compact K-vs-decision summary across Qwen3 sizes on v2 prompts. |

## 其他

| 文件 | 说明 |
| --- | --- |
| [seglib.py](seglib.py) | Segmentation helpers copied verbatim from mech_gate_test.py (frozen judge-gating segmentation). |
