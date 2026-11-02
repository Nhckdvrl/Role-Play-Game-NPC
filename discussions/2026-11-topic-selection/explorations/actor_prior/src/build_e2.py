"""E2: recognize vs predict vs enact on the same role-value dilemmas.

recognize - third person: which option better reflects this person's core value?
predict   - third person: which option will this person most likely choose?
enact     - second person: you are this person; which option do you take?
All framings get the identical role description + explicit core value + options.
"""
import itertools
import json
from pathlib import Path

from build_e1 import short_role

ROOT = Path.home() / "rp_prior"
Q = {
    "recognize": ("Here is a description of a person.", "Which option better reflects this person's core value? Answer with the letter only."),
    "predict": ("Here is a description of a person.", "Which option will this person most likely choose? Answer with the letter only."),
    "enact": ("You are the following person.", "Decide what you do. Answer with the letter of your choice only."),
}


def main():
    rows = json.load(open(ROOT / "data/rolecde_all.json"))
    out = []
    for r in rows:
        for diff, d in r["dilemmas"].items():
            for frame, swap in itertools.product(Q, (0, 1)):
                role_opt, norm_opt = d["option_B"], d["option_A"]
                first, second = (norm_opt, role_opt) if swap == 0 else (role_opt, norm_opt)
                head, q = Q[frame]
                who = "Your" if frame == "enact" else "This person's"
                body = (f"{head}\n{short_role(r['expanded_role'])}\n\n{who} core value: {r['personal_value']}\n\n"
                        f"Situation: {r['scenario']}\n{d['description']}\n\nOption A: {first}\nOption B: {second}\n\n{q}")
                out.append({"pid": r["id"], "cat": r["role_category_name"], "diff": diff, "cond": frame,
                            "swap": swap, "para": 0, "role_letter": "B" if swap == 0 else "A", "prompt": body})
    with open(ROOT / "data/e2_prompts.jsonl", "w") as f:
        for i, x in enumerate(out):
            f.write(json.dumps({"id": i, **x}, ensure_ascii=False) + "\n")
    print(len(out), "prompts")


if __name__ == "__main__":
    main()
