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

from .config import DEFAULT_IMAGE, DEFAULT_STYLE, DEFAULT_VOICE, ROOT

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass
class Beat:
    id: str
    text: str
    image_prompt: str
    role: str = ""
    index: int = 0

    @property
    def filename(self):
        return f"{self.id}.png"


@dataclass
class Script:
    path: Path
    topic: str
    slug: str
    style_lock: str
    beats: list
    style: dict
    image: dict
    voice: dict
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

    def image_path(self, beat):
        return self.assets_dir / beat.filename

    def prompt_for(self, beat):
        """The only place image prompts are assembled. style_lock always wins
        the trailing position so it reads as the art direction."""
        return f"{beat.image_prompt}, {self.style_lock}"

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

    raw_beats = data.get("beats") or []
    if not raw_beats:
        _fail("script has no beats")

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

        beats.append(Beat(id=bid, text=text, image_prompt=prompt,
                          role=b.get("role", ""), index=i))

    style_lock = (data.get("style_lock") or "").strip()
    if not style_lock:
        _fail("style_lock is required -- it is what keeps reels looking alike")

    style = dict(DEFAULT_STYLE)
    style.update(data.get("style") or {})

    image = dict(DEFAULT_IMAGE)
    image.update(data.get("image") or {})

    voice = dict(DEFAULT_VOICE)
    voice.update(data.get("voice") or {})
    if not voice.get("reference_id"):
        _fail("voice.reference_id is required -- pick a voice at fish.audio")

    return Script(
        path=path,
        topic=data.get("topic", slug),
        slug=slug,
        style_lock=style_lock,
        beats=beats,
        style=style,
        image=image,
        voice=voice,
        music=data.get("music"),
        raw=data,
    )
