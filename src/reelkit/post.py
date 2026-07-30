"""
Assemble the description that goes beside the reel in the feed.

Not to be confused with the captions burned into the picture -- those are
stitch.py's job and are configured under style.caption_*. This is the text a
viewer reads under the video, and it is kept in the script because the words
that sell a reel are worth versioning alongside the reel itself.

No network. Writing the file is the whole feature; posting stays manual.
"""

from .config import ROOT

# Instagram counts 30, TikTok fewer. Past that the app silently drops them,
# which looks like the tags "not working" rather than like a limit.
MAX_HASHTAGS = 30


def hashtags(post):
    """Normalise however the tags were written into '#tag' form.

    Accepts a list or one space-separated string, with or without leading
    hashes, because a script is hand-edited and both spellings feel natural.
    """
    raw = post.get("hashtags") or []
    if isinstance(raw, str):
        raw = raw.split()

    out, seen = [], set()
    for tag in raw:
        tag = str(tag).strip().lstrip("#").strip()
        if not tag:
            continue
        key = tag.lower()
        if key in seen:          # duplicates are wasted slots, not an error
            continue
        seen.add(key)
        out.append("#" + tag)
    return out


def render(script):
    """Caption then tags, separated by a blank line -- one copy, one paste."""
    caption = (script.post.get("caption") or "").strip()
    tags = hashtags(script.post)

    blocks = []
    if caption:
        blocks.append(caption)
    if tags:
        blocks.append(" ".join(tags))
    return ("\n\n".join(blocks) + "\n") if blocks else ""


def write(script):
    """Write assets/<slug>/post.txt. Returns the path, or None if the script
    has nothing to say yet."""
    tags = hashtags(script.post)
    if len(tags) > MAX_HASHTAGS:
        print(f"  ! {len(tags)} hashtags -- most apps keep only the first "
              f"{MAX_HASHTAGS}, the rest are dropped silently")

    text = render(script)
    if not text:
        print("  ! no post.caption in the script -- posting will need one "
              "written by hand")
        return None

    path = script.post_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"  post text -> {path.relative_to(ROOT)}  "
          f"({len(text.split())} words, {len(tags)} tags)")
    return path
