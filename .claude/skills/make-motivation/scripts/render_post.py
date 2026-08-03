#!/usr/bin/env python3
"""
Render one motivation post -- a carousel of PNGs, or a still reel mp4.

    python3 .claude/skills/make-motivation/scripts/render_post.py \
        scripts/motivation/day-01-carousel.json

Everything a slide needs is in the spec json. This script owns the parts that
must not drift between posts: the palette, the ink/accent pairing, the
Instagram safe box, and the single font size shared across a carousel. Those
are the things that make ten posts look like one account instead of ten
accidents, and they are exactly the things a model re-deciding them by hand
gets subtly wrong.

Output goes to out/motivation/day-<NN>/<type>/.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[4]
FONT_REGULAR = Path("/System/Library/Fonts/Supplemental/Comic Sans MS.ttf")
FONT_BOLD = Path("/System/Library/Fonts/Supplemental/Comic Sans MS Bold.ttf")
AUDIO_DIR = ROOT / "assets" / "motivation-audio"
PLAN_PATH = ROOT / "list-motivation.md"

# Background -> ink -> accent. The ink is fixed per background because contrast
# is not a taste question; the accent is the one colour allowed to shout, and
# it is only ever used on a word or two.
PALETTE = {
    "lavender":    {"bg": "#D5BCFE", "ink": "#33435F", "accent": "#0B3E89"},
    "royal-blue":  {"bg": "#0B3E89", "ink": "#FFFFFF", "accent": "#EFB143"},
    "slate-navy":  {"bg": "#33435F", "ink": "#FFFFFF", "accent": "#EFB143"},
    "warm-beige":  {"bg": "#E6C6A1", "ink": "#33435F", "accent": "#E32434"},
    "mustard":     {"bg": "#EFB143", "ink": "#33435F", "accent": "#0B3E89"},
    "red":         {"bg": "#E32434", "ink": "#FFFFFF", "accent": "#E6C6A1"},
}

CAROUSEL = {"w": 1080, "h": 1350, "top": 130, "bottom": 150, "side": 100}
# A reel is read past Instagram's own chrome: the caption block eats the bottom
# of the frame and the audio strip the top, so the safe box is much tighter.
REEL = {"w": 1080, "h": 1920, "top": 300, "bottom": 480, "side": 110}

# Autofit ranges per tier. Hero is the line someone reads while scrolling past;
# body is the argument; kicker is the small aside.
TIERS = {"hero": (78, 132), "body": (54, 96), "kicker": (40, 66)}
# A hero line that wraps six times stops being a hero line -- it becomes a
# paragraph in a big font. Capping the line count makes the fitter shrink the
# type instead of stacking it, which is what actually reads well at thumbnail
# size. If a slide needs more lines than this, the text is too long, not the
# font too big.
MAX_LINES = {"hero": 4, "body": 6, "kicker": 5}
LINE_SPACING = 1.28
MIN_LINES_APART = 1  # no two neighbouring slides in the same vertical slot

POSITIONS = ["top", "upper", "center", "lower", "bottom"]
HIGHLIGHT_RE = re.compile(r"\[([^\[\]]+)\]")


def die(msg):
    raise SystemExit(f"render_post: {msg}")


# ---------------------------------------------------------------- text layout

def _font(size, bold):
    path = FONT_BOLD if bold else FONT_REGULAR
    if not path.exists():
        die(f"font missing: {path}. Comic Sans MS ships with macOS Office "
            f"fonts; install it or point FONT_REGULAR at a copy.")
    return ImageFont.truetype(str(path), size)


def _strip(text):
    """Text as it renders -- highlight brackets are markup, not characters."""
    return HIGHLIGHT_RE.sub(r"\1", text)


def _wrap(draw, text, font, max_w):
    """Greedy wrap on the rendered text. Honours explicit \n."""
    lines = []
    for para in _strip(text).split("\n"):
        words, line = para.split(), ""
        if not words:
            lines.append("")
            continue
        for w in words:
            trial = f"{line} {w}".strip()
            if draw.textlength(trial, font=font) <= max_w or not line:
                line = trial
            else:
                lines.append(line)
                line = w
        lines.append(line)
    return lines


def _fits(draw, text, size, bold, box, max_lines=None):
    font = _font(size, bold)
    lines = _wrap(draw, text, font, box["w"])
    height = len(lines) * size * LINE_SPACING
    too_wide = any(draw.textlength(l, font=font) > box["w"] for l in lines)
    too_many = max_lines is not None and len(lines) > max_lines
    ok = (not too_wide) and (not too_many) and height <= box["h"]
    return ok, lines


def fit_size(draw, text, tier, bold, box):
    """Largest size in the tier that fits, or None if even the floor overflows.

    Returned per slide and then reduced to one number for the whole carousel --
    slides that each picked their own best size look like a pile of unrelated
    images, which is the single most common way these posts read as cheap.
    """
    lo, hi = TIERS[tier]
    # An explicit \n is the author saying where the reader pauses. Honour it:
    # prefer the largest size at which the wrapper adds no breaks of its own,
    # because a forced break plus an accidental one is how a line ends up
    # reading "not".
    forced = len(_strip(text).split("\n"))
    if forced > 1:
        for size in range(hi, lo - 1, -2):
            ok, lines = _fits(draw, text, size, bold, box, MAX_LINES[tier])
            if ok and len(lines) == forced:
                return size

    for size in range(hi, lo - 1, -2):
        ok, _ = _fits(draw, text, size, bold, box, MAX_LINES[tier])
        if ok:
            return size
    # Fall back to the line cap being advisory rather than failing outright:
    # a slide that only overflows the cap is still renderable, a slide that
    # overflows the box is not.
    for size in range(hi, lo - 1, -2):
        ok, _ = _fits(draw, text, size, bold, box)
        if ok:
            return size
    return None


# ---------------------------------------------------------------- composition

def _safe_box(canvas):
    return {
        "x": canvas["side"],
        "y": canvas["top"],
        "w": canvas["w"] - 2 * canvas["side"],
        "h": canvas["h"] - canvas["top"] - canvas["bottom"],
    }


def _block_origin(position, box, block_h):
    slack = max(0, box["h"] - block_h)
    frac = {"top": 0.0, "upper": 0.28, "center": 0.5,
            "lower": 0.72, "bottom": 1.0}[position]
    return box["y"] + slack * frac


def _draw_line(draw, line, spans, x, y, font, ink, accent):
    """Draw one wrapped line, colouring any [highlighted] runs in accent."""
    cursor = x
    for text, hot in spans:
        if not text:
            continue
        draw.text((cursor, y), text, font=font, fill=accent if hot else ink)
        cursor += draw.textlength(text, font=font)


def _spans_for_lines(text, lines):
    """Map highlight ranges from the source text onto the wrapped lines.

    Wrapping happens on the stripped text, so the offsets line up as long as we
    walk both in the same order.
    """
    flat = _strip(text)
    hot = [False] * len(flat)
    out_i = 0
    i = 0
    while i < len(text):
        if text[i] == "[":
            j = text.find("]", i)
            if j == -1:
                hot[out_i] = False
                out_i += 1
                i += 1
                continue
            for k in range(i + 1, j):
                hot[out_i] = True
                out_i += 1
            i = j + 1
        else:
            if out_i < len(hot):
                hot[out_i] = False
            out_i += 1
            i += 1

    result, pos = [], 0
    for line in lines:
        # Skip the whitespace the wrapper consumed between lines.
        while pos < len(flat) and flat[pos] != line[:1] and line:
            pos += 1
        spans, run, run_hot = [], "", None
        for ch in line:
            h = hot[pos] if pos < len(hot) else False
            if run_hot is None or h == run_hot:
                run += ch
                run_hot = h
            else:
                spans.append((run, run_hot))
                run, run_hot = ch, h
            pos += 1
        if run:
            spans.append((run, run_hot))
        result.append(spans or [(line, False)])
    return result


def render_slide(text, tier, size, position, colors, canvas, bold, align,
                 out_path):
    img = Image.new("RGB", (canvas["w"], canvas["h"]), colors["bg"])
    draw = ImageDraw.Draw(img)
    box = _safe_box(canvas)
    font = _font(size, bold)
    lines = _wrap(draw, text, font, box["w"])
    spans = _spans_for_lines(text, lines)
    step = size * LINE_SPACING
    y = _block_origin(position, box, len(lines) * step)

    for line, line_spans in zip(lines, spans):
        w = draw.textlength(line, font=font)
        if align == "center":
            x = box["x"] + (box["w"] - w) / 2
        elif align == "right":
            x = box["x"] + box["w"] - w
        else:
            x = box["x"]
        _draw_line(draw, line, line_spans, x, y, font,
                   colors["ink"], colors["accent"])
        y += step

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")

    # A hand-placed \n on a paragraph that also wraps is nearly always wrong:
    # the break lands where the author meant it and then the wrapper adds
    # another one somewhere else, which is how you get a line reading "not".
    if "\n" in _strip(text) and len(lines) > len(_strip(text).split("\n")):
        print(f"    ! forced line breaks in {out_path.name} are also being "
              f"wrapped -- shorten the lines or drop the \\n")
    return out_path


# ---------------------------------------------------------------- positioning

def auto_positions(slides, seed):
    """Vertical slot per slide, when the spec did not pin one.

    Varied so the carousel does not read as one image duplicated, but drawn
    from a fixed rotation and never repeating a neighbour -- random placement
    reads as sloppy, and identical placement reads as a template.
    """
    rotation = ["center", "top", "lower", "upper", "bottom"]
    start = seed % len(rotation)
    out, prev = [], None
    for i, s in enumerate(slides):
        if s.get("position") and s["position"] != "auto":
            pos = s["position"]
        else:
            pos = rotation[(start + i) % len(rotation)]
            if pos == prev:
                pos = rotation[(start + i + 1) % len(rotation)]
        if pos not in POSITIONS:
            die(f"slide {i + 1}: unknown position {pos!r}, "
                f"expected one of {POSITIONS}")
        out.append(pos)
        prev = pos
    return out


# ---------------------------------------------------------------- audio / mp4

def pick_audio(spec):
    if spec.get("audio"):
        p = (ROOT / spec["audio"]).resolve()
        if not p.exists():
            die(f"audio not found: {p}")
        return p
    tracks = sorted(
        p for p in AUDIO_DIR.glob("*")
        if p.suffix.lower() in {".mp3", ".m4a", ".wav", ".aac"}
    )
    if not tracks:
        return None
    # Deterministic per slug: the same reel re-rendered keeps its own track.
    idx = sum(ord(c) for c in spec["slug"]) % len(tracks)
    return tracks[idx]


def render_reel_mp4(frame, audio, duration, out_path):
    if not shutil.which("ffmpeg"):
        die("ffmpeg not on PATH")
    fade = min(1.5, duration / 6)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-loop", "1", "-i", str(frame)]
    if audio:
        cmd += ["-stream_loop", "-1", "-i", str(audio)]
    cmd += ["-t", f"{duration}",
            "-vf", "format=yuv420p",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-r", "30", "-pix_fmt", "yuv420p"]
    if audio:
        cmd += ["-af", f"afade=in:st=0:d={fade},"
                       f"afade=out:st={duration - fade:.2f}:d={fade}",
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-shortest"]
    else:
        cmd += ["-an"]
    cmd += [str(out_path)]
    subprocess.run(cmd, check=True)
    return out_path


# ---------------------------------------------------------------- plan ticking

def mark_done(spec):
    """Flip this post's line in list-motivation.md. True if the file changed.

    Keyed off files that now exist rather than off anyone's intention, for the
    same reason make-reel does it: a missed tick means the next run rebuilds a
    post that already shipped.
    """
    if not PLAN_PATH.exists():
        return False
    want = " ".join(re.findall(r"[a-z0-9]+", spec["topic"].lower()))
    if not want:
        return False
    lines = PLAN_PATH.read_text(encoding="utf-8").splitlines(keepends=True)
    for i, line in enumerate(lines):
        if not line.startswith("- [ ]"):
            continue
        norm = " ".join(re.findall(r"[a-z0-9]+", line.lower()))
        if want in norm:
            lines[i] = line.replace("- [ ]", "- [x]", 1)
            PLAN_PATH.write_text("".join(lines), encoding="utf-8")
            return True
    return False


# ---------------------------------------------------------------- entry points

def _colors(spec):
    name = spec.get("color")
    if name not in PALETTE:
        die(f"color {name!r} is not in the palette: {sorted(PALETTE)}")
    return PALETTE[name]


def _out_dir(spec, kind):
    return ROOT / "out" / "motivation" / f"day-{int(spec['day']):02d}" / kind


def do_carousel(spec, outdir):
    slides = spec.get("slides") or []
    if not 4 <= len(slides) <= 8:
        die(f"a carousel needs 4-8 slides, got {len(slides)}")
    colors = _colors(spec)
    align = spec.get("align", "center")
    box = _safe_box(CAROUSEL)
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))

    # One size per tier across the whole carousel: the smallest that every
    # slide in that tier can live with.
    fitted = {}
    for i, s in enumerate(slides):
        tier = s.get("tier", "hero" if i == 0 else "body")
        if tier not in TIERS:
            die(f"slide {i + 1}: unknown tier {tier!r}")
        bold = s.get("bold", tier == "hero")
        size = fit_size(probe, s["text"], tier, bold, box)
        if size is None:
            die(f"slide {i + 1} does not fit even at {TIERS[tier][0]}px. "
                f"Cut it down -- a slide nobody can read at arm's length is "
                f"not a slide.\n    {s['text'][:90]}")
        fitted.setdefault(tier, []).append(size)
    sizes = {t: min(v) for t, v in fitted.items()}

    positions = auto_positions(slides, sum(ord(c) for c in spec["slug"]))
    written = []
    for i, s in enumerate(slides):
        tier = s.get("tier", "hero" if i == 0 else "body")
        bold = s.get("bold", tier == "hero")
        path = outdir / f"{spec['slug']}-{i + 1:02d}.png"
        render_slide(s["text"], tier, sizes[tier], positions[i], colors,
                     CAROUSEL, bold, align, path)
        written.append(path)
        print(f"  slide {i + 1}/{len(slides)}  {tier:6} {sizes[tier]}px  "
              f"{positions[i]:6}  {path.name}")
    return written


def do_reel(spec, outdir):
    colors = _colors(spec)
    text = spec.get("text")
    if not text:
        die("a reel spec needs a `text` field")
    duration = float(spec.get("duration", 11))
    box = _safe_box(REEL)
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    tier = spec.get("tier", "hero")
    bold = spec.get("bold", True)
    size = fit_size(probe, text, tier, bold, box)
    if size is None:
        die(f"the reel text does not fit at {TIERS[tier][0]}px. A reel holds "
            f"one thought -- cut it.\n    {text[:90]}")
    position = spec.get("position", "center")
    if position == "auto":
        position = "center"

    frame = outdir / f"{spec['slug']}-frame.png"
    render_slide(text, tier, size, position, colors, REEL, bold,
                 spec.get("align", "center"), frame)
    print(f"  frame  {tier} {size}px  {position}  {frame.name}")

    audio = pick_audio(spec)
    print(f"  audio  {audio.name if audio else 'NONE (silent mp4)'}")
    mp4 = render_reel_mp4(frame, audio, duration, outdir / f"{spec['slug']}.mp4")
    print(f"  video  {duration:g}s  {mp4}")
    return [frame, mp4]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("spec", help="path to scripts/motivation/<name>.json")
    ap.add_argument("--no-tick", action="store_true",
                    help="do not tick the idea off list-motivation.md")
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    for key in ("day", "type", "slug", "topic", "color"):
        if not spec.get(key):
            die(f"spec is missing required key {key!r}")
    kind = spec["type"]
    if kind not in {"carousel", "reel"}:
        die(f"type must be carousel or reel, got {kind!r}")

    # Not created up front: a spec that fails validation should not leave an
    # empty day folder behind looking like a post that exists.
    outdir = _out_dir(spec, kind)
    print(f"== day {int(spec['day']):02d} {kind}  {spec['slug']}  "
          f"[{spec['color']}]")

    files = do_carousel(spec, outdir) if kind == "carousel" \
        else do_reel(spec, outdir)

    caption = spec.get("caption")
    if caption:
        (outdir / "post.txt").write_text(caption.rstrip() + "\n",
                                         encoding="utf-8")
        print(f"  post   {outdir / 'post.txt'}")
    else:
        print("  ! no caption in the spec -- post.txt not written")

    if not args.no_tick:
        print("  plan   " + ("ticked off in list-motivation.md"
                             if mark_done(spec)
                             else f"! nothing unchecked matches "
                                  f"{spec['topic']!r}"))
    print(f"  done   {len(files)} file(s) in {outdir}")


if __name__ == "__main__":
    main()
