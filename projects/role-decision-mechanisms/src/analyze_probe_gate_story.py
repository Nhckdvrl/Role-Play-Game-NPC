"""Probe gating on real-novel injection stories (E3 set, near position, original order, first 100 items).
Shift of P(target) relative to the uninjected story under the SAME condition (base or gated); classification of the
injected sentence (self should be kept: score >= 0; other should be gated: score < 0); fraction of story sentences gated.
usage: analyze_probe_gate_story.py STORY_GATE.jsonl"""
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1])]
none = {r["item"]: r for r in rows if r["src"] == "none"}
print(sys.argv[1].split("/")[-1])
for src in ("self", "other"):
    R = [r for r in rows if r["src"] == src and r["item"] in none]
    b = sum(r["base"] - none[r["item"]]["base"] for r in R) / len(R)
    g = sum(r["gated"] - none[r["item"]]["gated"] for r in R) / len(R)
    kept = sum((r["inj_score"] is not None and r["inj_score"] >= 0) for r in R) / len(R)
    print(f"{src:5s} n={len(R)}  shift base {b:+.3f}  gated {g:+.3f}   injected sentence kept (score>=0): {kept:.2f}")
fr = [r["n_gated"] / max(1, r["n_lines"]) for r in rows]
print(f"fraction of story sentences gated: {sum(fr) / len(fr):.2f}")
