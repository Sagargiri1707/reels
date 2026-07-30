"""
Tick an idea off list.md once its reel actually exists.

This used to be a step in the make-reel skill, which meant it was a step a
model had to remember at the end of a long run -- and it got missed. A missed
tick is not cosmetic: the next run picks the first unchecked idea, so it
rebuilds the reel that already exists and pays for the images a second time.

So the build does it, keyed off the rendered mp4 rather than off anyone's
intention. No network, no git.
"""

import re

from .config import ROOT

PLAN_PATH = ROOT / "list.md"

# `- [ ] **Day 2 — The planet where it rains glass, sideways**`
# The title is matched loosely because list.md is hand-edited and the dash
# between "Day N" and the title has been both a hyphen and an em dash.
CHECKBOX_RE = r"^- \[ \] (\*\*.*?%s.*?\*\*)\s*$"


def _norm(text):
    """Compare on words only. Punctuation, dashes and case all drift between
    the plan and the script's topic field; the words do not."""
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def find_entry(topic, path=None):
    """The unchecked line whose title matches this topic, or None.

    Matches on normalised words so `Day 2 — The planet where it rains glass,
    sideways` still resolves from a topic of `The planet where it rains glass,
    sideways`.
    """
    path = path or PLAN_PATH
    if not path.exists():
        return None

    want = _norm(topic)
    if not want:
        return None

    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if not line.startswith("- [ ]"):
            continue
        if want in _norm(line):
            return i
    return None


def mark_done(script, path=None):
    """Flip this script's idea to `- [x]`. Returns True if the file changed.

    Silent about ideas it cannot find: a reel built from a one-off topic that
    was never in the plan is a normal thing to do, not an error.
    """
    path = path or PLAN_PATH
    line_no = find_entry(script.topic, path)
    if line_no is None:
        return False

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    lines[line_no] = lines[line_no].replace("- [ ]", "- [x]", 1)
    path.write_text("".join(lines), encoding="utf-8")
    return True
