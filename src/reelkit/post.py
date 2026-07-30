"""
Assemble the description that goes beside the reel in the feed.

Not to be confused with the captions burned into the picture -- those are
stitch.py's job and are configured under style.caption_*. This is the text a
viewer reads under the video, and it is kept in the script because the words
that sell a reel are worth versioning alongside the reel itself.

No network. Writing the file is the whole feature; posting stays manual.
"""

import re

from .config import ROOT

# Instagram counts 30, TikTok fewer. Past that the app silently drops them,
# which looks like the tags "not working" rather than like a limit.
MAX_HASHTAGS = 30

TAG_RE = re.compile(r"#\w+")


def count_hashtags(text):
    """How many tags the caption carries. Only used to warn -- the caption is
    written the way it will be pasted, so nothing here rewrites it."""
    return len(TAG_RE.findall(text))


def render(script):
    """The caption is the post, tags and all. One field, one copy, one paste."""
    return (script.post.get("caption") or "").strip()


def write(script):
    """Write assets/<slug>/post.txt. Returns the path, or None if the script
    has nothing to say yet."""
    text = render(script)
    if not text:
        print("  ! no post.caption in the script -- posting will need one "
              "written by hand")
        return None

    tags = count_hashtags(text)
    if tags > MAX_HASHTAGS:
        print(f"  ! {tags} hashtags -- most apps keep only the first "
              f"{MAX_HASHTAGS}, the rest are dropped silently")
    text += "\n"

    path = script.post_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"  post text -> {path.relative_to(ROOT)}  "
          f"({len(text.split())} words, {tags} tags)")
    return path
