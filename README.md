# reelkit — narrated image-sequence Reels

Pipeline for `facts_by_sagar`. You write one JSON file per reel; the scripts
handle voice, timing and render.

```
script.json  →  make_audio.py  →  [generate images]  →  render_reel.py  →  reel.mp4
```

The important design decision: **beat durations come from the audio, not from
you.** You never write "3 seconds" anywhere. TTS produces the line, the renderer
measures it, and the image holds for exactly that long. Rewriting a line
re-times the whole reel automatically.

---

## Setup

```bash
# ffmpeg is the only hard dependency
brew install ffmpeg          # mac
sudo apt install ffmpeg      # linux
```

Fonts: the captions default to **Poppins**. Install it (free on Google Fonts)
or change `caption_font` in the script's `style` block to something you have.

---

## 1. Write the script

Copy `script.json` and edit. Each beat needs `text`, `image`, `audio`, and
`image_prompt`. Keep every line to one sentence — 8–14 words is the sweet spot.

Structure that works for this format:

| beat | job |
|---|---|
| 1 | **hook** — the surprising claim, on its own. No "in this video". |
| 2 | setup — what the list is |
| 3…n | one fact per beat |
| last | CTA |

Total target: **30–45s**. The renderer warns above 90s.

## 2. Voiceover

```bash
export ELEVEN_API_KEY=...
python3 make_audio.py script.json --backend eleven --voice <voice_id>
```

Files already present are skipped, so to re-record one line, delete just that
mp3 and re-run. **Use the same voice ID forever** — it's as much of a brand
asset as the visual style.

Cheaper options that work fine for this: OpenAI's TTS (`--backend openai`), or
Kokoro / Piper running locally for free if volume gets high.

## 3. Images

Generate one per beat into `images/`, named to match the script.

The whole trick is **style-locking**. Every prompt you send is:

```
<the beat's image_prompt>, <the script's style_lock>
```

`style_lock` in the example is the doodle look:

> minimal black ink doodle illustration, thin uniform line weight, simple
> stick-figure and flat-shape style, no shading, no gradients, no colour except
> black lines, plain off-white paper background #F2EDE4, generous white space,
> centred composition, hand-drawn cartoon feel

Three things that keep it consistent across reels:

1. **Never change the style_lock string.** Save it once; it is your art director.
2. **Fix the seed** if your generator supports it. Same seed + same style block
   = the same "hand" drawing every image.
3. **Keep a reference image.** Once you get one you love, feed it back as a
   style/image reference on every future generation. This matters more than
   prompt wording.

Square (1:1) images are ideal — the renderer fits them into the upper frame and
pads with the paper colour, so the artwork and background blend seamlessly.

## 4. Render

```bash
python3 render_reel.py script.json -o reel.mp4
```

Output is 1080×1920, 30fps, with slow alternating Ken Burns motion on each
image and burned-in captions. Add `--keep` to inspect intermediates in `build/`.

Background music: set `"music": "music/bed.mp3"` in the script. It loops and is
ducked to 8% under the voice.

## 5. Cover frame and caption

A finished mp4 is not a finished post. Two more things ship with it, both
local and free, and `build` produces them automatically:

```bash
python3 reel.py build  scripts/gravity-01.json     # mp4 + cover + caption
python3 reel.py thumb  scripts/gravity-01.json     # covers only
python3 reel.py post   scripts/gravity-01.json     # caption only
```

**Cover frame.** `thumb` grabs one candidate per beat from the *rendered*
video — so what you pick is exactly what a viewer sees, crop and Ken Burns
position included — and writes them to `assets/<slug>/thumbs/` along with a
`contact.jpg` sheet showing all of them at once. One is promoted to
`out/<slug>-thumb.jpg`. Which one:

1. `--beat 07` on the command line, for trying an alternative
2. `post.thumbnail_beat` in the script, once you have decided
3. otherwise beat 1 — the hook is what the script was written to open on

**Caption.** The `post` block holds the description that sits beside the reel
in the feed. Note this is *not* the burned-in subtitles; those are the
`style.caption_*` keys further down.

```json
"post": {
  "caption": "Gravity isn't pulling you down...\n\nOne fact a day. Follow.",
  "hashtags": ["gravity", "physics", "space"],
  "thumbnail_beat": "01"
}
```

Hashtags may be written with or without the `#`, as a list or one
space-separated string; duplicates are dropped. The rendered result is written
to `assets/<slug>/post.txt`, ready to copy in one go.

---

## Tuning

Everything lives in the `style` block of `script.json` (defaults in
`render_reel.py`):

| key | what it does |
|---|---|
| `bg` | paper colour — must match your image background |
| `image_box_w` / `image_box_h` / `image_top` | artwork size and position |
| `zoom_amount` | Ken Burns drift, `0.09` ≈ subtle. `0` disables |
| `zoom_supersample` | `2` is fine; `3` is smoother and slower |
| `caption_size` / `caption_margin_v` | caption size and height off the bottom |
| `caption_words_per_chunk` | `3` gives that punchy 2–3 word cadence |
| `gap` | breathing room after each line, in seconds |

**Caption timing.** By default each beat's text is split into chunks spread
evenly across the beat — close enough to feel synced. If you want true
word-level sync, add a `words` array to a beat:

```json
"words": [{"w": "Mars", "start": 0.0, "end": 0.34}, ...]
```

ElevenLabs' `with-timestamps` endpoint and Whisper both return these. Wire that
in once and the captions snap perfectly to the voice.

---

## Batching

Once the look is locked, one reel is: write JSON (10 min) → run three commands.
Keep a `topics.md` backlog and a `facts/` folder of verified claims, and batch
a week at a time.

**Add a verification step before render.** A facts account lives or dies on
being right — one confidently wrong reel gets screenshotted and dunked on. Put
a source link next to every claim in your script file. The format ignores extra
JSON keys, so add `"source": "https://..."` to each beat.
