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


# How a beat's final prompt is arrived at.
#
# "assembled" is the original shape: the beat carries a scene fragment and
# prompt_for welds the anchor, the lock, the paper and the text rule onto it at
# render time.
#
# "full" is the shape dolze-server's handdrawn carousel uses: one authoring pass
# writes every beat's complete, self-contained prompt in one go -- lock pasted
# verbatim, canvas, paper and text rule already inside it -- and the pipeline
# sends that string to the image model untouched. The point of it is that the
# prompt the model sees is the prompt sitting in the file, so a frame that came
# back wrong is debugged by reading the script rather than by re-deriving what
# the code appended.
PROMPT_FORMATS = ("assembled", "full")

# Image models will happily letter a frame with invented captions and gibberish
# unless told not to, so every prompt ends with one of these two rules. A beat
# opts into lettering by naming the exact words; everything else stays wordless.
# The marker is the part a full prompt is checked for -- the skill may phrase
# the rest of the clause its own way, but this half has to be in there.
NO_TEXT_MARKER = "no letters and no numbers"
NO_TEXT_RULE = f"no text, {NO_TEXT_MARKER} anywhere in the image"
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
ANCHOR_RULE = "the scene belongs to {anchor} and must visibly read as part of it"


@dataclass
class Beat:
    id: str
    text: str
    image_prompt: str
    role: str = ""
    index: int = 0
    image_text: str = ""
    # Defaults to the script's mode. Per beat because the outro is written by
    # the pipeline, not by the authoring pass, so it stays assembled even in a
    # full-prompt script -- see DEFAULT_OUTRO.
    prompt_format: str = "assembled"
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
    prompt_format: str
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

    @property
    def canvas(self):
        """The pixel canvas as the image model is told about it, e.g. 1152x2048.
        None when image_size is a fal preset name rather than a size."""
        size = self.image.get("image_size")
        if not isinstance(size, dict):
            return None
        return f"{size['width']}x{size['height']}"

    def prompt_for(self, beat):
        """The only place image prompts are assembled. Scene first, then the
        subject anchor that keeps it on topic, then the art direction, then the
        paper, and the text rule last because it is the one the model most needs
        to obey.

        A full-format beat skips all of that: its prompt was written complete
        and goes to the model exactly as written."""
        if beat.prompt_format == "full":
            return beat.image_prompt

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


def _check_full_prompt(beat, style_lock, canvas, paper):
    """A full prompt carries everything itself, so nothing downstream can put
    back what the authoring pass left out. These four things are the ones the
    pipeline used to guarantee by appending them; checking them here is what
    keeps 'written by hand once' from quietly becoming 'drifted apart'.

    All of it is a substring check on purpose -- the loader is not trying to
    grade the writing, only to prove the load-bearing clauses are present."""
    p = beat.image_prompt
    where = f"beat {beat.id} is prompt_format 'full' but its image_prompt"

    if style_lock not in p:
        _fail(f"{where} does not contain style_lock verbatim -- paste the lock "
              f"into every prompt, unreworded, or the frames stop matching")

    if canvas and canvas not in p:
        _fail(f"{where} never states the canvas {canvas!r}; the model follows "
              f"the prompt text over the size parameter and will compose wide")

    if paper and paper["hex"].lower() not in p.lower():
        _fail(f"{where} does not name this beat's paper colour {paper['hex']} "
              f"({paper['name']}); paper rotates by beat position, so beat "
              f"{beat.index} has to be the {beat.index}th tone")

    if beat.image_text:
        if beat.image_text not in p:
            _fail(f"{where} does not contain the image_text {beat.image_text!r} "
                  f"it is supposed to letter into the frame")
    elif NO_TEXT_MARKER not in p:
        _fail(f"{where} has no text rule -- a prompt that never forbids "
              f"lettering comes back captioned in invented gibberish. Say "
              f"{NO_TEXT_MARKER!r} in it, or set image_text")


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

    prompt_format = data.get("prompt_format") or "assembled"
    if prompt_format not in PROMPT_FORMATS:
        _fail(f"prompt_format {prompt_format!r} must be one of "
              f"{', '.join(PROMPT_FORMATS)}")

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

        beat_format = b.get("prompt_format") or prompt_format
        if beat_format not in PROMPT_FORMATS:
            _fail(f"beat {bid} prompt_format {beat_format!r} must be one of "
                  f"{', '.join(PROMPT_FORMATS)}")

        beats.append(Beat(id=bid, text=text, image_prompt=prompt,
                          role=b.get("role", ""), index=i,
                          image_text=image_text,
                          prompt_format=beat_format,
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

    s = Script(
        path=path,
        topic=data.get("topic", slug),
        slug=slug,
        style_lock=style_lock,
        subject_anchor=subject_anchor,
        beats=beats,
        prompt_format=prompt_format,
        style=style,
        image=image,
        voice=voice,
        post=post,
        music=data.get("music"),
        raw=data,
    )

    # Checked here rather than in the beat loop because a full prompt is judged
    # against the canvas and the paper rotation, and both of those are only
    # known once the image config is resolved.
    for beat in s.beats:
        if beat.prompt_format == "full":
            _check_full_prompt(beat, style_lock, s.canvas, s.paper_for(beat))

    return s
