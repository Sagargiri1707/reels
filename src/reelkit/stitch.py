"""
Assemble the final vertical video with ffmpeg.

One silent segment per beat with a slow alternating Ken Burns move, concatenated,
then the single narration track and burned-in captions muxed over the top.
Durations come from timeline.py, so the cuts land on the voice.
"""

from .ffmpeg import require_captions, run
from .timeline import caption_chunks


def hex_to_ass(hex_color, alpha="00"):
    """#RRGGBB -> ASS &HAABBGGRR."""
    h = hex_color.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{alpha}{b}{g}{r}".upper()


def ts(seconds):
    """Seconds -> ASS timestamp H:MM:SS.cc"""
    cs = int(round(max(seconds, 0.0) * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def build_ass(spans, style, out_path):
    """Write the caption track using the real word timings."""
    W, H = style["width"], style["height"]
    primary = hex_to_ass(style["caption_color"])
    outline = hex_to_ass(style["caption_outline"])
    back = hex_to_ass(style["caption_shadow"], alpha="60")

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{style["caption_font"]},{style["caption_size"]},{primary},{primary},{outline},{back},-1,0,0,0,100,100,0,0,1,{style["caption_outline_w"]},0,2,90,90,{style["caption_margin_v"]},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    lines = []
    for span in spans:
        for start, end, text in caption_chunks(span, style["caption_words_per_chunk"]):
            if style["caption_upper"]:
                text = text.upper()
            # ASS treats braces as override blocks and newlines as literal.
            text = text.replace("{", "(").replace("}", ")").replace("\n", " ")
            lines.append(f"Dialogue: 0,{ts(start)},{ts(end)},Cap,,0,0,0,,{text}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)


def build_segment(script, span, image_path, build_dir):
    """Render one beat to a silent mp4 with a slow Ken Burns move."""
    style = script.style
    W, H, FPS = style["width"], style["height"], style["fps"]
    dur = span.duration
    frames = max(2, int(round(dur * FPS)))
    seg = build_dir / f"seg_{span.index:03d}.mp4"

    # Fit the artwork into a safe box, sat on the paper-coloured canvas.
    box_w = int(W * style["image_box_w"])
    box_h = int(H * style["image_box_h"])
    top = int(H * style["image_top"])

    # Alternate the zoom direction so consecutive beats don't feel identical.
    amp = style["zoom_amount"]
    if span.index % 2 == 0:
        z = f"1+{amp}*on/{frames}"
    else:
        z = f"{1 + amp}-{amp}*on/{frames}"

    # Upscale before zoompan, otherwise the pan visibly stair-steps.
    ss = style["zoom_supersample"]

    vf = (
        f"scale={box_w}:{box_h}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:{top}:color={style['bg']},"
        f"scale={W * ss}:{H * ss}:flags=bicubic,"
        f"zoompan=z='{z}'"
        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        f":d={frames}:s={W}x{H}:fps={FPS},"
        f"setsar=1,format=yuv420p"
    )

    run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-loop", "1", "-i", str(image_path),
        "-t", f"{dur:.4f}",
        "-vf", vf,
        "-r", str(FPS),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        str(seg),
    ])
    return seg


def render(script, spans, out=None, keep=False, captions=True):
    style = script.style
    build_dir = script.build_dir
    build_dir.mkdir(parents=True, exist_ok=True)
    if captions:
        require_captions()   # before spending minutes encoding segments

    total = spans[-1].end
    print(f"total runtime {total:.2f}s")
    if total > 90:
        print("  ! over 90s - long for a Reel, consider cutting beats")

    by_id = {b.id: b for b in script.beats}
    segs = []
    for span in spans:
        beat = by_id[span.id]
        print(f"  beat {span.index + 1}/{len(spans)}  {span.duration:5.2f}s  "
              f"{beat.text[:44]}")
        segs.append(build_segment(script, span, script.image_path(beat), build_dir))

    # --- stitch the video ------------------------------------------------
    concat_v = build_dir / "concat_v.txt"
    concat_v.write_text(
        "\n".join(f"file '{s.as_posix()}'" for s in segs) + "\n", encoding="utf-8")
    silent = build_dir / "silent.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", str(concat_v), "-c", "copy", str(silent)])

    # --- captions --------------------------------------------------------
    # Always written, so the file can be inspected or muxed in later even when
    # this ffmpeg cannot burn it.
    ass = build_dir / "captions.ass"
    cards = build_ass(spans, style, ass)
    print(f"  {cards} caption cards"
          + ("" if captions else "  (written but not burned in)"))

    # --- final mux -------------------------------------------------------
    out = out or script.out_path
    out.parent.mkdir(parents=True, exist_ok=True)

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent)]
    if captions:
        # libavfilter parses these characters inside a filter argument.
        ass_arg = (ass.as_posix().replace("\\", "\\\\").replace(":", r"\:")
                   .replace("'", r"\'").replace(",", r"\,"))
        filters = [f"[0:v]ass=filename={ass_arg}[v]"]
    else:
        filters = ["[0:v]null[v]"]
    amix = []

    cmd += ["-i", str(script.narration_path)]
    amix.append(f"[1:a]volume={style['voice_volume']}[a0]")

    music = script.music_path
    if music:
        if not music.exists():
            raise SystemExit(f"music file not found: {music}")
        cmd += ["-stream_loop", "-1", "-i", str(music)]
        amix.append(f"[2:a]volume={style['music_volume']}[a1]")

    if len(amix) == 2:
        filters += amix + ["[a0][a1]amix=inputs=2:duration=first:"
                           "dropout_transition=0,dynaudnorm=p=0.85[a]"]
    else:
        filters += amix + ["[a0]anull[a]"]

    cmd += ["-filter_complex", ";".join(filters), "-map", "[v]", "-map", "[a]",
            "-c:a", "aac", "-b:a", "192k",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-t", f"{total:.4f}", str(out)]

    run(cmd)

    if not keep:
        for pattern in ("seg_*.mp4", "concat_v.txt"):
            for f in build_dir.glob(pattern):
                f.unlink()

    print(f"\ndone -> {out}  ({total:.1f}s, {style['width']}x{style['height']})")
    return out
