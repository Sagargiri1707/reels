"""
One narration file for the whole reel, from fish.audio, with timings.

The plain /v1/tts endpoint returns audio and nothing else, which would leave
the stitcher with no idea when each beat starts. /v1/tts/stream/with-timestamp
returns the same audio plus an alignment, so a single continuous read can
still be cut into beats exactly.

Per fish's docs the alignment is a *snapshot* keyed by chunk_seq, not a delta:
a chunk can report its alignment more than once as more audio renders, and the
later report replaces the earlier one. The audio frames are deltas and are
always appended.
"""

import base64
import json

from .config import FISH_TTS_TIMESTAMP, require_env
from .ffmpeg import probe_duration
from .http import stream_sse

# How far the alignment may disagree with the real file before we refuse to
# build a video that would drift out of sync.
MAX_DRIFT_SEC = 0.75


def _headers(script):
    return {
        "Authorization": f"Bearer {require_env('FISH_API_KEY')}",
        "model": script.voice["model"],
    }


def _payload(script):
    body = {
        "text": script.narration_text,
        "reference_id": script.voice["reference_id"],
        "format": script.voice.get("format", "mp3"),
        "latency": script.voice.get("latency", "normal"),
    }
    prosody = script.voice.get("prosody")
    if prosody:
        body["prosody"] = prosody
    return body


def _flatten(chunks):
    """
    chunks: {chunk_seq: (offset_sec, alignment)}  ->  flat segment list on the
    global timeline, in order.
    """
    segments = []
    for seq in sorted(chunks):
        offset, alignment = chunks[seq]
        for seg in (alignment or {}).get("segments") or []:
            text = (seg.get("text") or "").strip()
            if not text:
                continue
            segments.append({
                "text": text,
                "start": float(seg["start"]) + offset,
                "end": float(seg["end"]) + offset,
            })
    return segments


def synth(script, force=False):
    """
    Write assets/<slug>/narration.mp3 and alignment.json. Skipped when both
    already exist, because this call costs money.
    """
    if script.narration_path.exists() and script.alignment_path.exists() \
            and not force:
        print(f"  skip  {script.narration_path.name} (cached)")
        return json.loads(script.alignment_path.read_text(encoding="utf-8"))

    script.assets_dir.mkdir(parents=True, exist_ok=True)
    text = script.narration_text
    print(f"  tts   {len(text)} chars, voice {script.voice['reference_id']}")

    audio = bytearray()
    chunks = {}
    events = 0

    for event in stream_sse(FISH_TTS_TIMESTAMP, _payload(script), _headers(script)):
        events += 1
        b64 = event.get("audio_base64")
        if b64:
            audio.extend(base64.b64decode(b64))

        alignment = event.get("alignment")
        if alignment:
            seq = event.get("chunk_seq", 0)
            offset = float(event.get("chunk_audio_offset_sec") or 0.0)
            chunks[seq] = (offset, alignment)   # replace, never append

    if not audio:
        raise SystemExit(
            f"fish returned no audio across {events} events -- "
            "check FISH_API_KEY and voice.reference_id"
        )

    segments = _flatten(chunks)
    if not segments:
        raise SystemExit(
            "fish returned audio but no alignment segments. Without timings "
            "the beats cannot be cut; check that the `model` header supports "
            f"timestamps (got {script.voice['model']!r})."
        )

    script.narration_path.write_bytes(bytes(audio))
    real = probe_duration(script.narration_path)
    claimed = max(s["end"] for s in segments)

    # Loud, because a silent mismatch here desyncs the whole video.
    if abs(real - claimed) > MAX_DRIFT_SEC:
        raise SystemExit(
            f"alignment disagrees with the audio: file is {real:.2f}s but the "
            f"last segment ends at {claimed:.2f}s (drift {real - claimed:+.2f}s).\n"
            "The SSE stream was probably truncated. Re-run with --force."
        )

    data = {
        "audio_duration": real,
        "segments": segments,
        "text": text,
        "voice": script.voice["reference_id"],
        "model": script.voice["model"],
    }
    script.alignment_path.write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8")

    print(f"  wrote {script.narration_path.name}  {real:.2f}s, "
          f"{len(segments)} segments")
    return data


def load_alignment(script):
    if not script.alignment_path.exists():
        raise SystemExit(
            f"missing {script.alignment_path}\n"
            f"run: python3 reel.py voice {script.path.name}"
        )
    return json.loads(script.alignment_path.read_text(encoding="utf-8"))
