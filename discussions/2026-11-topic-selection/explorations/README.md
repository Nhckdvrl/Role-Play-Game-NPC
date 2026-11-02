# Explorations from the 2026-11 topic selection (archived)

Code and result summaries of the two experiments run during topic selection. Both are closed; see [../SUMMARY.md](../SUMMARY.md) for findings and why they were stopped. Large inputs and raw outputs stay on the cluster (`~/rp_voice/`, `~/rp_prior/`) and can be rebuilt from the scripts.

| Folder | Experiment | Contents |
| --- | --- | --- |
| `voice/` | Character voice: speaker identification of generated next lines (Friends, Cornell Movie-Dialogs) | `src/build_slots.py` (slots from the public corpora), `src/gen.py` (vLLM generation), `src/score.py` (char n-gram fidelity and separability), `src/inspect_amp.py`; `results_score_all.txt` |
| `actor_prior/` | Role-value dilemmas (RoleCDE public subset): next-token A/B preference under persona manipulations, E1–E6 | `src/build_e1.py`, `src/build_e2.py` (prompt builders; E3–E6 builders were inline and are described in ../10_ZONE_ACTOR_PRIOR.md), `src/score_ab.py` (vLLM scoring), `src/analyze_*.py`, `src/make_results.sh`; `results/e1–e6.txt`; `data/pers_negpos.json` (537 prosocial personality sections from RoleCDE with Qwen3-32B antisocial rewrites, Apache-2.0 source) |

Models used: Qwen3-8B, Qwen3-8B-Base, Qwen3-32B, Llama-3.1-8B-Instruct (NousResearch copy), Gemma-3-12B-it, Mistral-Small-24B-Instruct-2501 (pilot only). The downloaded OLMo-2 stage checkpoints were deleted when the work was closed.
