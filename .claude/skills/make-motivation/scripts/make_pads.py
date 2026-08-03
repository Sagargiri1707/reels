#!/usr/bin/env python3
"""
Generate the calm background pads a still reel sits on.

    python3 .claude/skills/make-motivation/scripts/make_pads.py

Writes assets/motivation-audio/pad-<key>.mp3. These are deliberately plain --
a slow, low, slightly detuned chord with a soft pulse. The point is something
that reads as "intentional silence" under a quote, not music anyone notices.

Drop your own mp3/wav files into the same folder and they get picked up
automatically; render_post.py just takes whatever audio is there. Delete the
generated pads once you have real tracks.
"""

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "assets" / "motivation-audio"
SECONDS = 40  # longer than any reel, so nothing has to loop mid-post

# Root, third, fifth of a quiet minor-ish chord, one octave apart on top.
PADS = {
    "a-minor":  (110.00, 130.81, 164.81, 220.00),
    "d-minor":  (146.83, 174.61, 220.00, 293.66),
    "e-minor":  (82.41, 123.47, 164.81, 246.94),
    "g-major":  (98.00, 123.47, 146.83, 196.00),
}


def build(name, freqs):
    out = OUT / f"pad-{name}.mp3"
    inputs = []
    for f in freqs:
        inputs += ["-f", "lavfi", "-i", f"sine=frequency={f}:duration={SECONDS}"]
    chain = (
        f"amix=inputs={len(freqs)}:weights=1 0.55 0.35 0.22:normalize=0,"
        # Slow tremolo keeps it breathing instead of droning.
        "tremolo=f=0.12:d=0.35,"
        # Roll off everything bright -- sines are harsh in the top end.
        "lowpass=f=900,"
        "aecho=0.8:0.88:900|1700:0.25|0.15,"
        f"afade=in:st=0:d=3,afade=out:st={SECONDS - 4}:d=4,"
        "volume=0.16"
    )
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
           "-filter_complex", chain, "-c:a", "libmp3lame", "-b:a", "160k",
           str(out)]
    subprocess.run(cmd, check=True)
    print(f"  {out.relative_to(ROOT)}  {out.stat().st_size // 1024} KB")


def main():
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not on PATH")
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"== pads -> {OUT.relative_to(ROOT)}")
    for name, freqs in PADS.items():
        build(name, freqs)


if __name__ == "__main__":
    main()
