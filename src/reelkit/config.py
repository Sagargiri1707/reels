"""
Defaults, environment loading and path layout.

Nothing here talks to the network or the filesystem beyond reading .env.
"""

import os
from pathlib import Path

# Repo root = two levels up from src/reelkit/config.py
ROOT = Path(__file__).resolve().parents[2]

FAL_QUEUE = "https://queue.fal.run"
FISH_TTS_TIMESTAMP = "https://api.fish.audio/v1/tts/stream/with-timestamp"


DEFAULT_STYLE = {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "bg": "#F2EDE4",

    # "cover" fills the whole frame, cropping any overflow, so the artwork's
    # own background IS the reel background and no seam can show. "contain"
    # is the old behaviour: fit the art into a box and pad around it, which
    # only looks right when the image background exactly matches `bg`.
    "image_fit": "cover",

    "image_box_w": 0.92,      # contain only: artwork width as a frame fraction
    "image_box_h": 0.62,      # contain only: artwork height as a frame fraction
    "image_top": 0.13,        # contain only: artwork offset from the top

    "zoom_amount": 0.09,      # how much Ken Burns drift per beat
    "zoom_supersample": 2,    # raise to 3 for silkier motion, slower render

    "caption_font": "Poppins",
    "caption_size": 62,
    "caption_color": "#1A1A1A",
    "caption_outline": "#F2EDE4",
    "caption_outline_w": 4,
    "caption_shadow": "#000000",
    "caption_margin_v": 380,  # distance from the bottom edge
    "caption_words_per_chunk": 3,
    "caption_upper": True,

    "music_volume": 0.08,     # ducked under the voiceover
    "voice_volume": 1.0,
}

DEFAULT_IMAGE = {
    "model": "openai/gpt-image-2",
    # fal accepts a preset name or {"width": w, "height": h}. Concrete sizes
    # must be multiples of 16 and total 0.65-8.3 megapixels. Exact 9:16 needs
    # w=144k, h=256k; k=8 gives 1152x2048, which matches the reel frame and
    # downscales into 1080x1920 rather than being blown up.
    "image_size": {"width": 1152, "height": 2048},
    "quality": "low",
    "output_format": "png",

    # How many beats are rendered at once. Every beat is an independent fal job
    # -- the old one-at-a-time loop spent a whole reel's wall clock waiting on
    # a queue it could have been waiting on in parallel. Kept modest rather than
    # unbounded: a dozen simultaneous jobs is a good way to meet a rate limit
    # halfway through a reel and pay for the half that landed.
    "concurrency": 4,

    # Rotated one per beat, in order, wrapping at the end. Twelve frames on one
    # paper tone read as a single held image no matter how different the
    # drawings are; changing the paper underneath is what makes a cut land.
    # All muted and light enough that black ink still reads on top, and ordered
    # so no two neighbours sit close on the wheel.
    "palette": [
        {"name": "warm off-white", "hex": "#F2EDE4"},
        {"name": "pale slate blue", "hex": "#DFE4E9"},
        {"name": "soft sand",       "hex": "#EFE3D8"},
        {"name": "pale sage",       "hex": "#E4E9DF"},
        {"name": "faint rose grey", "hex": "#EDE1E4"},
        {"name": "cool pale grey",  "hex": "#E5E7E6"},
    ],
}

DEFAULT_VOICE = {
    # The free tier of the same s2.1-pro voice model. Same reference_id, same
    # read; it costs nothing, so it is what a script gets unless it names
    # otherwise. The paid tier is one string away if the queue ever bites.
    "model": "s2.1-pro-free",
    "reference_id": None,
    "format": "mp3",
    "latency": "normal",
    "prosody": {"speed": 1.0},
}

# What you paste into the app, and which frame sells it in the feed. Kept in
# the script so the words and the cover travel with the video that needs them.
# Note the namespace: these are NOT the burned-in subtitles, which live in
# DEFAULT_STYLE as caption_font / caption_size / caption_* above.
DEFAULT_POST = {
    # The whole feed description, hashtags written inline with their own '#'.
    # One field because it is pasted as one block -- splitting it meant the
    # script never showed what the post would actually look like.
    "caption": "",
    "thumbnail_beat": None,   # beat id to use as cover; None = the hook beat
    "thumbnail_quality": 2,   # ffmpeg -q:v, 2 is near-lossless jpeg
}


# The sign-off, appended as a real final beat to every reel by script.load().
# It is here rather than copied into each script on purpose: it has to be word
# for word and frame for frame identical every time, because that repetition is
# the entire point -- a viewer should recognise the ending before it finishes.
# A script can drop it with "outro": false.
DEFAULT_OUTRO = {
    "id": "outro",
    "role": "outro",
    "text": "One of these every day. Follow so you do not miss tomorrow.",
    "image_prompt": (
        "a chunky red enamel push button on a round metal base, drawn head on "
        "and pressed halfway down, a hand withdrawing from it at the frame edge"
    ),
    "image_text": "FOLLOW",
    "anchored": False,   # identical in every reel, so no per-reel subject
    # Written by the pipeline, not by the authoring pass, so it stays assembled
    # even in a full-prompt script: it is one fragment shared by every reel and
    # its paper tone falls out of how many beats the reel happens to have, so
    # there is no one finished prompt that could be baked here.
    "prompt_format": "assembled",
}


def load_dotenv(path=None):
    """
    Read KEY=VALUE lines from .env into os.environ without overwriting
    anything already set. Deliberately tiny -- no external dependency, and
    values never get logged.
    """
    path = Path(path) if path else ROOT / ".env"
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def require_env(name):
    load_dotenv()
    value = os.environ.get(name)
    if not value:
        raise SystemExit(
            f"{name} is not set. Put it in {ROOT / '.env'} or export it."
        )
    return value
