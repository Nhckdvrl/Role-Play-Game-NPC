"""Prompt builders and output parsers shared by the first-batch experiments."""
import re

HER_FORMAT = """===Output Format===
Your output should include thought, speech, and action in this two-part structure:

1. System Thinking: A single block at the very beginning, wrapped in <system_thinking> and </system_thinking>. This is third-person analysis of how to portray the character.

2. Role-play Response: The character's actual response including:
   - <role_thinking>inner thoughts</role_thinking> (invisible to others)
   - <role_action>physical actions</role_action> (visible to others)
   - Speech (plain text, what the character says out loud)"""


def profile_block(profile):
    return "\n".join(f"- {s}" for s in profile)


def plain_system(name, profile):
    return (f"You are {name}. Stay fully in character as {name} and reply to the user as {name} "
            f"would, speaking in the first person.\n\n==={name}'s Profile===\n{profile_block(profile)}\n\n"
            f"Respond naturally and conversationally, as {name}.")


def her_system(name, profile, scene=None, user_name="Visitor", user_profile=None):
    """Mirrors HER chat_demo.build_system_prompt, minus the book/initial-thought fields."""
    scene = scene or f"A visitor has come to talk with {name} and asks a question."
    user_profile = user_profile or f"A curious person talking with {name}."
    return f"""You are role-playing as {name}.

==={name}'s Profile===
{profile_block(profile)}

===Current Scene===
{scene}

===The Person You Are Interacting With===
{user_name}: {user_profile}

===Instructions===
- Stay in character as {name} at all times
- Keep responses natural and engaging
- Respond from {name}'s perspective
- **IMPORTANT: Speak DIRECTLY to "{user_name}" using "you" (second person). Do NOT use third person.**

{HER_FORMAT}"""


def director_from_facts(name, query, facts):
    """Templated director block used for counterfactual director interventions."""
    lines = "\n".join(f"{i + 1}. {f}" for i, f in enumerate(facts))
    return (f"<system_thinking>\nThe visitor asks: \"{query}\". To answer as {name}, the reply should draw "
            f"on these profile facts:\n{lines}\n{name} should speak in a voice and attitude consistent "
            f"with the profile, directly to the visitor.\n</system_thinking>\n")


_TAG = lambda t: re.compile(rf"<{t}>(.*?)</{t}>", re.S)


def parse_her(full):
    """Split a HER-format completion (including the <system_thinking> prefix) into stages.

    visible = actions + speech (what the user would see); speech = plain text only.
    """
    sys_m = _TAG("system_thinking").search(full)
    director = sys_m.group(1).strip() if sys_m else ""
    rest = full[sys_m.end():] if sys_m else full
    ok = bool(sys_m)
    role_thinking = " ".join(m.strip() for m in _TAG("role_thinking").findall(rest))
    actions = [m.strip() for m in _TAG("role_action").findall(rest)]
    no_think = _TAG("role_thinking").sub(" ", rest)
    visible = _TAG("role_action").sub(lambda m: f"({m.group(1).strip()})", no_think)
    speech = _TAG("role_action").sub(" ", no_think)
    clean = lambda s: re.sub(r"\s+", " ", re.sub(r"</?(role_speech|system_thinking|role_thinking|role_action)>", " ", s)).strip()
    return {"director": director, "role_thinking": role_thinking, "actions": actions,
            "visible": clean(visible), "speech": clean(speech), "format_ok": ok}


def parse_native(full):
    """Qwen3 native thinking: '<think>...</think> answer' (the opening tag may be in the prompt)."""
    if "</think>" in full:
        think, ans = full.split("</think>", 1)
        think = think.replace("<think>", "").strip()
        return {"think": think, "visible": ans.strip(), "speech": ans.strip(), "format_ok": True}
    return {"think": full.replace("<think>", "").strip(), "visible": "", "speech": "", "format_ok": False}
