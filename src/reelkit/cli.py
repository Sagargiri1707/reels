"""
reelkit command line.

    python3 reel.py images  scripts/planets-01.json
    python3 reel.py voice   scripts/planets-01.json
    python3 reel.py stitch  scripts/planets-01.json
    python3 reel.py build   scripts/planets-01.json    # all three
"""

import argparse

from . import images, script as script_mod, stitch, timeline, voice
from .ffmpeg import require_tools


def _load(args):
    return script_mod.load(args.script)


def cmd_images(args):
    s = _load(args)
    only = set(args.only.split(",")) if args.only else None
    images.generate(s, force=args.force, only=only)


def cmd_voice(args):
    s = _load(args)
    voice.synth(s, force=args.force)


def _spans(s, even_split=False):
    alignment = voice.load_alignment(s)
    if even_split:
        return timeline.even_split(s.beats, float(alignment["audio_duration"]))
    try:
        return timeline.build(s.beats, alignment, strict=True)
    except timeline.AlignmentMismatch as e:
        raise SystemExit(f"timeline error:\n{e}") from None


def cmd_stitch(args):
    require_tools()
    s = _load(args)
    images.verify(s)
    spans = _spans(s, args.even_split)
    stitch.render(s, spans, out=args.out, keep=args.keep,
                  captions=args.captions)


def cmd_build(args):
    require_tools()
    s = _load(args)
    print(f"== {s.topic}  ({s.slug}, {len(s.beats)} beats)")
    print("-- images")
    images.generate(s, force=args.force)
    print("-- voice")
    voice.synth(s, force=args.force)
    print("-- stitch")
    images.verify(s)
    spans = _spans(s, args.even_split)
    stitch.render(s, spans, out=args.out, keep=args.keep,
                  captions=args.captions)


def cmd_timeline(args):
    """Print the cut points without rendering. Cheap sanity check."""
    s = _load(args)
    spans = _spans(s, args.even_split)
    by_id = {b.id: b for b in s.beats}
    for sp in spans:
        print(f"  {sp.id}  {sp.start:6.2f} -> {sp.end:6.2f}  "
              f"({sp.duration:5.2f}s)  {by_id[sp.id].text[:44]}")
    print(f"  total {spans[-1].end:.2f}s")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="reel", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_text, **flags):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("script", help="path to scripts/<reel>.json")
        if flags.get("force"):
            p.add_argument("--force", action="store_true",
                           help="regenerate even if cached (costs money)")
        if flags.get("render"):
            p.add_argument("-o", "--out", default=None, type=_path,
                           help="output mp4 (default out/<slug>.mp4)")
            p.add_argument("--keep", action="store_true",
                           help="keep intermediates in build/")
            p.add_argument("--no-captions", dest="captions",
                           action="store_false",
                           help="skip burned-in captions (ffmpeg without libass)")
        if flags.get("timing"):
            p.add_argument("--even-split", action="store_true",
                           help="ignore alignment, space beats by word count")
        if flags.get("only"):
            p.add_argument("--only", default=None,
                           help="comma separated beat ids to regenerate")
        p.set_defaults(fn=fn)
        return p

    add("images", cmd_images, "generate beat images with fal", force=True, only=True)
    add("voice", cmd_voice, "generate narration + alignment with fish", force=True)
    add("timeline", cmd_timeline, "print beat cut points", timing=True)
    add("stitch", cmd_stitch, "render the video", render=True, timing=True)
    add("build", cmd_build, "images + voice + stitch",
        force=True, render=True, timing=True)

    args = ap.parse_args(argv)
    args.fn(args)


def _path(value):
    from pathlib import Path
    return Path(value)


if __name__ == "__main__":
    main()
