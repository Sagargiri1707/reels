"""
Load and validate a reel script, and resolve every path it implies.

A script names beats; it does not name files. Image and audio paths are
derived from the slug and beat id so a script can never drift out of sync
with what is on disk.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .config import (DEFAULT_IMAGE, DEFAULT_OUTRO, DEFAULT_POST,
                     DEFAULT_STYLE, DEFAULT_VOICE, ROOT)

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


# Image models will happily letter a frame with invented captions and gibberish
# unless told not to, so every prompt ends with one of these two rules. A beat
# opts into lettering by naming the exact words; everything else stays wordless.
NO_TEXT_RULE = "no text, no letters and no numbers anywhere in the image"
TEXT_RULE = ('the only writing anywhere in the image is the exact word {words!r}, '
             'hand-lettered in plain block capitals on the surface it belongs to, '
             'with no other writing, caption or label of any kind')

# Long strings render as garbled lettering far more often than short ones, and a
# beat that needs a sentence on screen is a beat that should have been drawn.
MAX_IMAGE_TEXT = 24

# Every beat is written and rendered on its own, which is how a reel ends up as
# twelve unrelated pictures that each illustrate one sentence. The anchor is the
# one line that names what the whole reel is about, and it rides on every prompt
# so no frame can wander off the subject.
#
# Keep it soft. An earlier version demanded the scene "must visibly read as part
# of" the subject, and the model satisfied that by parking a tiny observatory in
# the corner of nearly every frame -- on topic, but a repeated watermark. The
# subject is supposed to arrive through the main object, not through scenery.
ANCHOR_RULE = "the object in the scene comes from the world of {anchor}"


@dataclass
class Beat:
    id: str
    text: str
    image_prompt: str
    role: str = ""
    index: int = 0
    image_text: str = ""
    # The sign-off is the same frame in every reel, so it must not pick up the
    # per-reel subject anchor -- an anchored outro would be a space button in
    # one reel and a kitchen button in the next.
    anchored: bool = True

    @property
    def filename(self):
        return f"{self.id}.png"


@dataclass
class Script:
    path: Path
    topic: str
    slug: str
    style_lock: str
    subject_anchor: str
    beats: list
    style: dict
    image: dict
    voice: dict
    post: dict = field(default_factory=dict)
    music: str = None
    raw: dict = field(default_factory=dict)

    # ---- derived paths -------------------------------------------------
    # assets/ is permanent: it holds everything that cost money to make.
    # build/ and out/ are disposable and gitignored.

    @property
    def assets_dir(self):
        return ROOT / "assets" / self.slug

    @property
    def build_dir(self):
        return ROOT / "build" / self.slug

    @property
    def out_path(self):
        return ROOT / "out" / f"{self.slug}.mp4"

    @property
    def narration_path(self):
        return self.assets_dir / "narration.mp3"

    @property
    def alignment_path(self):
        return self.assets_dir / "alignment.json"

    @property
    def manifest_path(self):
        return self.assets_dir / "manifest.json"

    @property
    def music_path(self):
        return (ROOT / self.music) if self.music else None

    @property
    def post_path(self):
        """The description to paste when posting. Lives in assets/ because it
        is written by hand and losing it means rewriting it."""
        return self.assets_dir / "post.txt"

    @property
    def thumbs_dir(self):
        return self.assets_dir / "thumbs"

    @property
    def thumb_path(self):
        """The promoted cover frame, next to the video it belongs to."""
        return ROOT / "out" / f"{self.slug}-thumb.jpg"

    def image_path(self, beat):
        return self.assets_dir / beat.filename

    def paper_for(self, beat):
        """Which paper tone this beat is drawn on. Rotating through the palette
        by position means neighbouring frames never share a background, which is
        the cheapest way to stop a reel reading as one long static image."""
        palette = self.image.get("palette") or []
        if not palette:
            return None
        return palette[beat.index % len(palette)]

    def prompt_for(self, beat):
        """The only place image prompts are assembled. Scene first, then the
        subject anchor that keeps it on topic, then the art direction, then the
        paper, and the text rule last because it is the one the model most needs
        to obey."""
        parts = [beat.image_prompt]
        if beat.anchored:
            parts.append(ANCHOR_RULE.format(anchor=self.subject_anchor))
        parts.append(self.style_lock)
        paper = self.paper_for(beat)
        if paper:
            parts.append(f"drawn on {paper['name']} paper, "
                         f"flat background colour {paper['hex']}")
        parts.append(TEXT_RULE.format(words=beat.image_text) if beat.image_text
                     else NO_TEXT_RULE)
        return ", ".join(parts)

    @property
    def narration_text(self):
        """One continuous read. Beat order is the timeline order."""
        return " ".join(b.text.strip() for b in self.beats)


def _fail(msg):
    raise SystemExit(f"script error: {msg}")


def load(path):
    path = Path(path).resolve()
    if not path.exists():
        _fail(f"no such file: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        _fail(f"{path.name} is not valid JSON: {e}")

    slug = data.get("slug") or path.stem
    if not SLUG_RE.match(slug):
        _fail(f"slug {slug!r} must be lowercase alphanumeric, dot, dash or underscore")

    raw_beats = list(data.get("beats") or [])
    if not raw_beats:
        _fail("script has no beats")

    # The sign-off is appended here, not written into each script, so it stays
    # identical across every reel and cannot drift one beat at a time. Adding
    # it as a real beat means narration, timeline, images and stitch all pick
    # it up with no special case anywhere downstream.
    outro = data.get("outro", True)
    if outro:
        raw_beats.append(dict(DEFAULT_OUTRO, **(outro if isinstance(outro, dict) else {})))

    beats, seen = [], set()
    for i, b in enumerate(raw_beats):
        bid = str(b.get("id") or f"{i + 1:02d}")
        if not ID_RE.match(bid):
            _fail(f"beat {i} has unusable id {bid!r}")
        if bid in seen:
            _fail(f"duplicate beat id {bid!r}")
        seen.add(bid)

        text = (b.get("text") or "").strip()
        if not text:
            _fail(f"beat {bid} has no text")
        prompt = (b.get("image_prompt") or "").strip()
        if not prompt:
            _fail(f"beat {bid} has no image_prompt")

        image_text = (b.get("image_text") or "").strip()
        if len(image_text) > MAX_IMAGE_TEXT:
            _fail(f"beat {bid} image_text is {len(image_text)} characters; keep it "
                  f"under {MAX_IMAGE_TEXT} or the model will garble it")

        beats.append(Beat(id=bid, text=text, image_prompt=prompt,
                          role=b.get("role", ""), index=i,
                          image_text=image_text,
                          anchored=b.get("anchored", True)))

    style_lock = (data.get("style_lock") or "").strip()
    if not style_lock:
        _fail("style_lock is required -- it is what keeps reels looking alike")

    subject_anchor = (data.get("subject_anchor") or "").strip()
    if not subject_anchor:
        _fail("subject_anchor is required -- without it every beat gets drawn "
              "as its own sentence and the reel stops looking like one story")

    style = dict(DEFAULT_STYLE)
    style.update(data.get("style") or {})

    image = dict(DEFAULT_IMAGE)
    image.update(data.get("image") or {})
    for i, paper in enumerate(image.get("palette") or []):
        if not isinstance(paper, dict) or not paper.get("name") or not paper.get("hex"):
            _fail(f"image.palette[{i}] needs both a name and a hex")

    voice = dict(DEFAULT_VOICE)
    voice.update(data.get("voice") or {})
    if not voice.get("reference_id"):
        _fail("voice.reference_id is required -- pick a voice at fish.audio")

    post = dict(DEFAULT_POST)
    post.update(data.get("post") or {})
    # Catch a bad cover-frame reference now, not after a full render.
    wanted = post.get("thumbnail_beat")
    if wanted is not None and str(wanted) not in seen:
        _fail(f"post.thumbnail_beat {wanted!r} is not a beat id in this script "
              f"(have: {', '.join(sorted(seen))})")

    return Script(
        path=path,
        topic=data.get("topic", slug),
        slug=slug,
        style_lock=style_lock,
        subject_anchor=subject_anchor,
        beats=beats,
        style=style,
        image=image,
        voice=voice,
        post=post,
        music=data.get("music"),
        raw=data,
    )
