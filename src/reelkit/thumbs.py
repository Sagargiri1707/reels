"""
Pull cover-frame candidates out of the finished video.

The frame that stops a scroll is a separate decision from the video that
follows it, so this offers one candidate per beat and promotes exactly one to
out/<slug>-thumb.jpg.

Frames come from the rendered mp4 rather than the source artwork on purpose:
what you pick is then exactly what a viewer sees, crop, Ken Burns position and
caption card included. Grabbing the original PNG would show a frame that never
appears in the video.
"""

import math
import shutil

from .config import ROOT
from .ffmpeg import run

CONTACT_WIDTH = 270   # per cell; a 12-beat sheet stays under 1100px wide
CONTACT_COLS = 4


def frame_time(span):
    """Sample each beat at its midpoint.

    The first frame of a beat is the weakest one available: the zoom has not
    moved yet and the beat's caption card may not have appeared. The midpoint
    is representative of what the beat actually looks like on screen.
    """
    return span.start + span.duration / 2


def extract(script, spans, video=None):
    """Write one candidate jpg per beat. Returns [(span, path)]."""
    video = video or script.out_path
    if not video.exists():
        raise SystemExit(
            f"no video to grab frames from: {video}\n"
            f"  render it first:  python3 reel.py build {script.path.name}"
        )

    out_dir = script.thumbs_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    quality = script.post.get("thumbnail_quality", 2)
    last = spans[-1].end

    made = []
    for span in spans:
        # Never seek past the end; the final beat's midpoint is safe but a
        # hand-edited span list is not guaranteed to be.
        at = min(frame_time(span), max(last - 0.05, 0.0))
        path = out_dir / f"{span.index + 1:02d}-{span.id}.jpg"
        run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-ss", f"{at:.3f}", "-i", str(video),
            "-frames:v", "1", "-q:v", str(quality),
            str(path),
        ])
        made.append((span, path))
    return made


def contact_sheet(script, made):
    """One image showing every candidate, so picking is a glance not a click
    through a folder. Auxiliary -- a failure here must not lose the render."""
    if len(made) < 2:
        return None

    paths = [p for _, p in made]
    cols = min(CONTACT_COLS, len(paths))
    rows = math.ceil(len(paths) / cols)
    out = script.thumbs_dir / "contact.jpg"

    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for p in paths:
        cmd += ["-i", str(p)]

    scaled = "".join(f"[{i}:v]scale={CONTACT_WIDTH}:-1[s{i}];"
                     for i in range(len(paths)))
    joined = "".join(f"[s{i}]" for i in range(len(paths)))
    graph = (f"{scaled}{joined}concat=n={len(paths)}:v=1:a=0[cat];"
             f"[cat]tile={cols}x{rows}:margin=8:padding=8[out]")

    cmd += ["-filter_complex", graph, "-map", "[out]",
            "-frames:v", "1", "-q:v", "3", str(out)]
    try:
        run(cmd)
    except SystemExit:
        print("  ! contact sheet failed -- the individual candidates in "
              f"{script.thumbs_dir.relative_to(ROOT)} are still good")
        return None
    return out


def choose(script, made, beat=None):
    """Which candidate becomes the cover. Pure, so the precedence rule can be
    tested without rendering anything.

    Precedence is flag, then the script's post.thumbnail_beat, then the first
    beat -- the hook is the default cover because it is the frame the script
    was built to open on.
    """
    wanted = beat or script.post.get("thumbnail_beat")
    if wanted is None:
        return made[0][1]

    for span, path in made:
        if span.id == str(wanted):
            return path

    ids = ", ".join(span.id for span, _ in made)
    raise SystemExit(f"no beat {wanted!r} in this reel -- have: {ids}")


def select(script, made, beat=None):
    """Promote one candidate to out/<slug>-thumb.jpg."""
    chosen = choose(script, made, beat=beat)
    dest = script.thumb_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(chosen, dest)
    return chosen, dest


def generate(script, spans, beat=None, video=None):
    made = extract(script, spans, video=video)
    sheet = contact_sheet(script, made)
    chosen, dest = select(script, made, beat=beat)

    print(f"  {len(made)} cover candidates -> "
          f"{script.thumbs_dir.relative_to(ROOT)}/")
    if sheet:
        print(f"  contact sheet -> {sheet.relative_to(ROOT)}")
    print(f"  cover ({chosen.stem}) -> {dest.relative_to(ROOT)}")
    return dest
