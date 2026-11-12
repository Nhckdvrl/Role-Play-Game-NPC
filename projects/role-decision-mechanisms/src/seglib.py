"""Segmentation helpers copied verbatim from mech_gate_test.py (frozen judge-gating segmentation)."""
import re


def sheet_lines(text):
    """(segment_text, char_start, owner_tag) for every fact segment in the context block, for card / json / prose.
    owner_tag is not used for gating (judge-based only); it is 'NA'."""
    starts = [text.find(k) for k in ("Characters in this story", "Game state:", "Background.") if text.find(k) >= 0]
    s0 = min(starts)
    s1 = text.rfind("Situation:")
    block = text[s0:s1]
    out = []
    if block.startswith("Characters in this story"):
        pos = s0
        for line in block.split("\n"):
            if line.startswith("- "):
                out.append((line[2:], pos + 2, "NA"))
            elif line.startswith("Attitudes: "):
                out.append((line[len("Attitudes: "):], pos + len("Attitudes: "), "NA"))
            pos += len(line) + 1
    elif block.startswith("Game state:"):
        pos = s0
        for line in block.split("\n"):
            m = re.match(r'^(\s*)"((?:[^"\\]|\\.)*)",?\s*$', line)
            if m:
                seg = m.group(2)
                out.append((seg, pos + len(m.group(1)) + 1, "NA"))
            pos += len(line) + 1
    else:
        for m in re.finditer(r"[^.!?\n]+(?:\"[^\"]*\")?[^.!?\n]*[.!?]", block):
            seg = m.group(0).strip()
            if len(seg) > 8 and not seg.startswith("Background"):
                out.append((seg, s0 + m.start() + (len(m.group(0)) - len(m.group(0).lstrip())), "NA"))
    return out


def dlg_sheet(r):
    """Clean story text for the judge, for dialogue formats (chatlog / chat): narrator content only."""
    if r["fmt"] == "chatlog":
        c = r["messages"][0]["content"]
        return c[c.find("Story so far:"):c.rfind("Situation:")].strip()
    us = [m["content"] for m in r["messages"][:-1] if m["role"] == "user"]
    us[0] = us[0][us[0].find("Story so far:"):]
    return "\n\n".join(us).strip()


def dlg_lines(r, text):
    """Fact lines (non-header story lines) located in the rendered text, in order."""
    out, cur = [], 0
    for line in dlg_sheet(r).split("\n"):
        line = line.strip()
        if len(line) <= 8 or line.startswith("[") or line.startswith("Story so far"):
            continue
        a = text.find(line, cur)
        if a < 0:
            continue
        out.append((line, a, "NA"))
        cur = a + len(line)
    return out
