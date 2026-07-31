# Pipeline

What runs, what it costs, and what to do when it breaks. Read this when a build fails or you need a flag.

## Commands

Every command takes a script path. `build` is the whole thing; the rest are the same stages individually, for retries.

| Command | Does | Costs money |
|---|---|---|
| `python3 reel.py build scripts/<slug>.json --no-captions` | images → voice → stitch → cover → post.txt → tick off `list.md` | yes (images, voice) |
| `python3 reel.py images <script> [--only 03,07] [--force]` | beat frames via fal | yes |
| `python3 reel.py voice <script> [--force]` | narration + word alignment via fish | free tier by default |
| `python3 reel.py timeline <script>` | prints beat cut points, no render | no |
| `python3 reel.py stitch <script> --no-captions` | the mp4, from cached images + voice | no |
| `python3 reel.py thumb <script> --beat 07` | cover frames from the rendered mp4 | no |
| `python3 reel.py post <script>` | writes and prints `assets/<slug>/post.txt` | no |

Caching is by content hash in `assets/<slug>/manifest.json`. A beat whose prompt is unchanged is skipped, so re-running `build` after a stitch failure re-renders nothing. `--force` overrides that and re-pays.

## Where things land

```
scripts/<slug>.json          what you author
assets/<slug>/               beat images, manifest.json, post.txt, thumbs/
build/<slug>/                intermediates, including the .ass subtitle file
out/<slug>.mp4               the reel
out/<slug>-thumb.jpg         the cover
```

## Config that matters

Defaults live in `src/reelkit/config.py`; a script's `style`/`image`/`voice` blocks override per key.

- `image.image_size` — `1152x2048`. Exact 9:16, downscales into the 1080x1920 frame rather than being blown up. The prompt must also *say* the canvas; the model trusts the text over the parameter.
- `image.palette` — six muted paper tones, rotated one per beat by position. A script that omits the key inherits all six.
- `image.concurrency` — 4 beats rendered at once. Every beat is an independent fal job and the time is queue wait, so this is wall-clock, not compute. Kept modest: a dozen simultaneous jobs is a good way to meet a rate limit halfway through a reel and pay for the half that landed.
- `voice.model` — omit it. The default is `s2.1-pro-free`, same voice, no cost. Some older scripts still name the paid tier.
- `voice.reference_id` — required, and it is the brand voice. Never change it.
- `style.caption_*` — the subtitles burned into the picture. Not `post.caption`, which is the feed description.
- `outro: false` — drops the appended sign-off beat. Only for a reel that genuinely should not have one.

## When it fails

**Script rejected at load.** The message starts `script error:` and names the beat and the missing clause. Every one of these is a prompt-contract violation — a reworded lock, a missing canvas, the wrong paper hex for that beat's position, no text rule. Fix the `scene` (or the beat's `image_text`), re-run `expand_prompts.py`, build again. Do not hand-patch the generated `image_prompt`; the next expansion overwrites it.

**Some images failed.** The run keeps and records everything that landed — that work is already paid for — and raises at the end naming the beats. Retry only those:

```bash
python3 reel.py images scripts/<slug>.json --only 03,07
```

Then `build` again; the cached beats are skipped.

**`timeline error:` on stitch.** The narration audio and the beat list disagree — usually a beat's `text` was edited after the voice was synthesised. Re-run `voice --force`.

**Burned-in captions.** `--no-captions` is required on this machine: its ffmpeg has no libass. The `.ass` file is still written to `build/<slug>/` and can be muxed later. Check with `ffmpeg -hide_banner -filters | grep ' ass '` — if that matches, drop the flag, because burned-in captions measurably help retention on muted autoplay.

**Missing key.** `FAL_KEY` / fish credentials come from `.env` at the repo root via `require_env`. Never print or commit them.

## Ticking off `list.md`

`src/reelkit/plan.py` flips the first unchecked entry whose title matches the script's `topic`, and the build calls it *after* the mp4 exists. Matching is on normalised words, so punctuation and dash style do not matter, but the words do.

This is deliberately not a step anyone has to remember: a missed tick means the next run picks the same idea and pays for the images a second time. If the build prints `! no unchecked list.md entry matches ...`, the `topic` string and the plan entry have drifted — report it, and do not hand-edit `list.md` to compensate.
