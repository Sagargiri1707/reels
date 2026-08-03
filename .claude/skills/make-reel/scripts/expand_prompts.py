#!/usr/bin/env python3
"""
Turn each beat's `scene` into its finished `image_prompt`.

    python3 .claude/skills/make-reel/scripts/expand_prompts.py scripts/<slug>.json

Scripts are written `prompt_format: "full"`, meaning the string in the file is
the string the image model sees. Six of its seven parts are constants -- the
canvas line, the anchor clause, the style lock, the paper tone for that beat's
position, the text rule and the avoid list -- and assembling them by hand is
where a reel drifts: one reworded lock, one paper tone counted off by one, one
beat that forgot the text rule and came back captioned in gibberish. All of
those are things `Script.load` rejects the whole script for, so the authoring
pass writes part 2 (`scene`) and this writes the rest.

Idempotent: re-run it after editing any scene. It only ever rewrites
`image_prompt`, and `scene` stays in the file so the next run has a source.
"""

import argparse
import json
import sys
from pathlib import Path


def _repo_root(start):
    """Walk up to the checkout, so the script can be run from anywhere."""
    for d in [start, *start.parents]:
        if (d / "reel.py").exists() and (d / "src" / "reelkit").is_dir():
            return d
    sys.exit("expand_prompts: cannot find the repo root (looked for reel.py)")


ROOT = _repo_root(Path(__file__).resolve())
sys.path.insert(0, str(ROOT / "src"))

from reelkit.config import DEFAULT_IMAGE  # noqa: E402

# Part 3, the two anchor forms. The grounded one names what to leave out as
# well as what to draw, because a beat about the everyday case fails in one
# specific way: the model keeps the reel's subject in frame to be helpful, and
# the viewer spends the beat wondering why Jupiter is on the windowsill.
ANCHORED = "the scene belongs to {anchor}, and must visibly read as part of it."
GROUNDED = ("this is an ordinary everyday scene and {leave_out}; it is the "
            "ordinary case the rest of the reel is measured against.")

# Part 6. NO_TEXT matches the marker script.py checks for; TEXT quotes the words
# so the loader's `image_text in prompt` check finds them verbatim.
NO_TEXT = "no text, no letters and no numbers anywhere in the image."
TEXT = ('the only writing anywhere in the image is the exact English word '
        '"{words}", hand-lettered in plain block capitals on the surface it '
        'belongs to, with no other writing, caption or label of any kind.')

# Part 7, identical on every beat of every reel. The bans track the failure
# list in the ian-xiaohei-scenes skill: it wants one real object on white with
# 小黑 acting on it, so what kills a frame is screenshots, UI, poster gradients
# and prop-pile compositions -- not mascots, which is the character itself.
AVOID = ("Avoid: full-page border or frame, page number, title, caption, "
         "watermark, gibberish or invented text, non-English lettering, "
         "screenshots, app or website UI, logos, gradients, vignette, grey or "
         "warm-white background, heavy drop shadows, neon or saturated colour, "
         "crowded composition of many props, flat vector icon look, sticker "
         "cut-out edges, several people, PPT or infographic layout.")


def _fail(msg):
    sys.exit(f"expand_prompts: {msg}")


def _canvas(image):
    size = image.get("image_size")
    if not isinstance(size, dict):
        _fail("image.image_size must be {\"width\": w, \"height\": h} -- a fal "
              "preset name gives the prompt no canvas to state")
    return f"{size['width']}x{size['height']}"


def _sentence(text):
    """Every part ends in one full stop, so the parts stay separable by eye."""
    text = " ".join(text.split()).rstrip(" .,;")
    return text + "."


def build_prompt(beat, index, *, anchor, lock, canvas, palette):
    scene = (beat.get("scene") or "").strip()
    if not scene:
        _fail(f"beat {beat.get('id')} has no `scene` -- that is the one part of "
              f"the prompt the authoring pass writes")

    if beat.get("anchored", True):
        anchor_part = ANCHORED.format(anchor=anchor.rstrip(" ."))
    else:
        leave_out = (beat.get("grounded") or "").strip().rstrip(" .")
        if not leave_out:
            _fail(f"beat {beat.get('id')} is anchored:false but has no "
                  f"`grounded` clause. Name what to leave out, e.g. "
                  f"\"contains no planet, telescope or other space object\" -- "
                  f"otherwise the model keeps the subject in frame and the "
                  f"grounding beat argues with its own narration")
        anchor_part = GROUNDED.format(leave_out=leave_out)

    paper = palette[index % len(palette)]
    words = (beat.get("image_text") or "").strip()

    return " ".join([
        f"9:16 vertical portrait canvas, {canvas}.",
        _sentence(scene),
        anchor_part,
        _sentence(lock),
        f"set on a seamless {paper['name']} studio surface, "
        f"flat background colour {paper['hex']}.",
        TEXT.format(words=words) if words else NO_TEXT,
        AVOID,
    ])


def expand(path, write=True):
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _fail(f"no such file: {path}")
    except json.JSONDecodeError as e:
        _fail(f"{path.name} is not valid JSON: {e}")

    lock = (data.get("style_lock") or "").strip()
    if not lock:
        _fail("style_lock is required -- copy it verbatim from "
              "scripts/8-planets-01.json")
    anchor = (data.get("subject_anchor") or "").strip()
    if not anchor:
        _fail("subject_anchor is required -- one line naming what the reel is "
              "about, in objects")

    image = dict(DEFAULT_IMAGE)
    image.update(data.get("image") or {})
    palette = image.get("palette") or []
    if not palette:
        _fail("image.palette is empty -- there is no paper tone to rotate")
    canvas = _canvas(image)

    beats = data.get("beats") or []
    if not beats:
        _fail("script has no beats")

    # Position counts authored beats from zero. The pipeline's sign-off beat is
    # appended at load time and stays assembled, so it is not counted here.
    for i, beat in enumerate(beats):
        beat["image_prompt"] = build_prompt(
            beat, i, anchor=anchor, lock=lock, canvas=canvas, palette=palette)

    data["prompt_format"] = "full"

    if write:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    for i, beat in enumerate(beats):
        paper = palette[i % len(palette)]
        words = (beat.get("image_text") or "").strip()
        flag = f"  text:{words}" if words else ""
        print(f"  {beat.get('id')}  {paper['hex']}  "
              f"{len(beat['image_prompt'].split()):3d}w{flag}")
    print(f"{len(beats)} prompts -> {path}")
    return data


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1].strip())
    ap.add_argument("script", help="path to scripts/<slug>.json")
    ap.add_argument("--dry-run", action="store_true",
                    help="build the prompts and report, but do not write")
    args = ap.parse_args(argv)
    expand(args.script, write=not args.dry_run)


if __name__ == "__main__":
    main()
