"""
reelkit command line.

    python3 reel.py images  scripts/planets-01.json
    python3 reel.py voice   scripts/planets-01.json
    python3 reel.py stitch  scripts/planets-01.json
    python3 reel.py thumb   scripts/planets-01.json    # cover frames
    python3 reel.py post    scripts/planets-01.json    # caption to paste
    python3 reel.py build   scripts/planets-01.json    # the whole thing
"""

import argparse

from . import (images, plan, post as post_mod, schedule, script as script_mod,
               stitch, thumbs, timeline, voice)
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


def cmd_thumb(args):
    """Cover frames from an already rendered video."""
    require_tools()
    s = _load(args)
    spans = _spans(s, args.even_split)
    thumbs.generate(s, spans, beat=args.beat, video=args.video)


def cmd_post(args):
    """Write (and show) the description to paste when posting."""
    s = _load(args)
    post_mod.write(s)
    text = post_mod.render(s)
    if text:
        print()
        print(text, end="")


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
    out = stitch.render(s, spans, out=args.out, keep=args.keep,
                        captions=args.captions)
    # Both are local ffmpeg / file writes, so they cost nothing and a reel is
    # not actually postable without them.
    print("-- cover")
    thumbs.generate(s, spans, beat=args.beat, video=out)
    print("-- post")
    post_mod.write(s)
    # The mp4 exists, so the idea is done. Doing this here rather than leaving
    # it to whoever ran the build is what stops the next run rebuilding the
    # same reel and paying for the images twice.
    print("-- plan")
    if plan.mark_done(s):
        print(f"  ticked off in list.md  ({s.topic})")
    else:
        print(f"  ! no unchecked list.md entry matches {s.topic!r} "
              f"-- nothing to tick off")


def cmd_publish(args):
    """Publish a finished out/ directory to Instagram right now."""
    from . import publish
    media_id = publish.publish_dir(args.dir, dry_run=args.dry_run,
                                   share_to_feed=args.share_to_feed)
    if media_id:
        print(f"published {media_id}")


def cmd_schedule(args):
    schedule.show(schedule.add(args.dir, args.at,
                               share_to_feed=args.share_to_feed))


def cmd_queue(args):
    if not args.run:
        schedule.show(schedule.load())
        return
    published, failed = schedule.run(dry_run=args.dry_run)
    if published or failed:
        print(f"{published} published, {failed} failed")


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
        if flags.get("cover"):
            p.add_argument("--beat", default=None,
                           help="beat id to use as the cover frame "
                                "(default: post.thumbnail_beat, else the hook)")
        if flags.get("source"):
            p.add_argument("--video", default=None, type=_path,
                           help="video to grab frames from "
                                "(default out/<slug>.mp4)")
        p.set_defaults(fn=fn)
        return p

    add("images", cmd_images, "generate beat images with fal", force=True, only=True)
    add("voice", cmd_voice, "generate narration + alignment with fish", force=True)
    add("timeline", cmd_timeline, "print beat cut points", timing=True)
    add("stitch", cmd_stitch, "render the video", render=True, timing=True)
    add("thumb", cmd_thumb, "pick cover frames from the rendered video",
        timing=True, cover=True, source=True)
    add("post", cmd_post, "write the caption + hashtags to paste")
    add("build", cmd_build, "images + voice + stitch + cover + caption",
        force=True, render=True, timing=True, cover=True)

    # Posting works on a finished out/ directory, not on a script, so these
    # three sit outside the add() helper and its `script` positional.
    pub = sub.add_parser("publish", help="post a finished out/ dir to Instagram now")
    pub.add_argument("dir", type=_path, help="e.g. out/motivation/day-01/carousel")
    pub.add_argument("--dry-run", action="store_true",
                     help="show what would be posted, call nothing")
    pub.add_argument("--no-feed", dest="share_to_feed", action="store_false",
                     help="reels only: keep it out of the main feed grid")
    pub.set_defaults(fn=cmd_publish)

    sch = sub.add_parser("schedule", help="queue a finished out/ dir for later")
    sch.add_argument("dir", type=_path)
    sch.add_argument("--at", required=True, help='local time, "2026-08-05 18:30"')
    sch.add_argument("--no-feed", dest="share_to_feed", action="store_false")
    sch.set_defaults(fn=cmd_schedule)

    q = sub.add_parser("queue", help="list the queue, or publish what is due")
    q.add_argument("--run", action="store_true", help="publish everything now due")
    q.add_argument("--dry-run", action="store_true")
    q.set_defaults(fn=cmd_queue)

    args = ap.parse_args(argv)
    args.fn(args)


def _path(value):
    from pathlib import Path
    return Path(value)


if __name__ == "__main__":
    main()
