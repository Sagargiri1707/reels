#!/usr/bin/env python3
"""
make_audio.py - generate one voiceover file per beat.

    export ELEVEN_API_KEY=...        # or OPENAI_API_KEY
    python3 make_audio.py script.json --backend eleven --voice <voice_id>

Writes audio/<id>.mp3 for every beat, which render_reel.py then uses to time
the video. Existing files are skipped unless you pass --force, so you can
re-record a single beat by deleting just that file.
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path


def tts_eleven(text, out, voice, model="eleven_multilingual_v2"):
    key = os.environ.get("ELEVEN_API_KEY")
    if not key:
        raise SystemExit("set ELEVEN_API_KEY")
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
        data=json.dumps({
            "text": text,
            "model_id": model,
            # lower stability = more expressive; raise it if delivery wanders
            "voice_settings": {"stability": 0.45, "similarity_boost": 0.8,
                               "style": 0.15, "use_speaker_boost": True},
        }).encode(),
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        out.write_bytes(r.read())


def tts_openai(text, out, voice="onyx", model="gpt-4o-mini-tts"):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("set OPENAI_API_KEY")
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=json.dumps({"model": model, "voice": voice,
                         "input": text, "response_format": "mp3"}).encode(),
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        out.write_bytes(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--backend", choices=["eleven", "openai"], default="eleven")
    ap.add_argument("--voice", default=None)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    path = Path(a.script).resolve()
    root = path.parent
    data = json.loads(path.read_text(encoding="utf-8"))
    (root / "audio").mkdir(exist_ok=True)

    for b in data["beats"]:
        out = root / b["audio"]
        if out.exists() and not a.force:
            print(f"  skip {out.name}")
            continue
        print(f"  tts  {out.name}  {b['text'][:50]}")
        if a.backend == "eleven":
            if not a.voice:
                raise SystemExit("--voice <voice_id> required for eleven")
            tts_eleven(b["text"], out, a.voice)
        else:
            tts_openai(b["text"], out, a.voice or "onyx")

    print("\ndone. now: python3 render_reel.py", path.name)


if __name__ == "__main__":
    main()
