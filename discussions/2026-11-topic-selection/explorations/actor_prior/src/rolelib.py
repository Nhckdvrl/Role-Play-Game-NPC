"""Shared persona-text helpers."""
import re
from build_e1 import short_role
HDR = re.compile(r"^\s*(?:\d+\.\s*\**|#{2,4}\s*|\*\*\d*\.?\s*)?[A-Z][A-Za-z &/]{3,40}(?:\*\*)?:?\**\s*$")


def no_personality(t):
    """Drop the 'Personality ...' section (any of the header styles used in RoleCDE profiles)."""
    out, skip = [], False
    for l in short_role(t).splitlines():
        if "ersonality" in l and len(l) < 60:
            skip = True
            continue
        if skip and HDR.match(l) and "ersonality" not in l:
            skip = False
        if not skip:
            out.append(l)
    return "\n".join(out)


def personality_section(t):
    """Return the 'Personality ...' section lines (header excluded)."""
    out, on = [], False
    for l in short_role(t).splitlines():
        if "ersonality" in l and len(l) < 60:
            on = True
            continue
        if on and HDR.match(l) and "ersonality" not in l:
            break
        if on and l.strip():
            out.append(l.rstrip())
    return "\n".join(out)
