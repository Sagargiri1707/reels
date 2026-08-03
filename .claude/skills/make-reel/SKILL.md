---
name: make-reel
description: End-to-end reel factory for this repo — one idea to a finished vertical mp4, cover frame and feed caption. Picks the next unchecked idea from list.md, writes scripts/<slug>.json, drafts the beats and narration, expands each scene into a full house-style image prompt, renders with reel.py, picks the cover, and writes the caption with hashtags. Use this whenever the user says "make a reel", "next reel", "build the next video", "new reel from the list", "do the next idea", "make a short", "make a video about X", or hands over a topic and wants a reel of it — including Instagram reels, TikToks and YouTube Shorts. Also use for any single piece of an existing reel: rewriting beats, narration or the hook, fixing or re-rolling image prompts, re-rendering the mp4, choosing a new thumbnail or cover frame, or writing the caption, hashtags and post text. If the request touches list.md, scripts/*.json, reel.py, beats, image prompts, style_lock, voiceover, subtitles, covers or captions, this skill owns it — use it rather than improvising a pipeline. Image prompts come from the `ian-xiaohei-scenes` skill; this skill only adds the reel-shaped deltas around it.
---

# Make Reel

One idea becomes one vertical mp4, its cover frame, and the text you paste beside it.

```
list.md idea → scripts/<slug>.json → images (fal) → narration (fish)
             → stitch (ffmpeg) → cover + post.txt → idea ticked off
```

You author exactly one artefact: the json. Everything downstream is `python3 reel.py build`.

## Read these before you write anything

| File | When |
|---|---|
| `references/script-writing.md` | Before the first beat. Story shape, the lesson, narration rules. |
| the `ian-xiaohei-scenes` skill | Before the first image prompt. The house look: 小黑 + real objects + one physical action + white space. Invoke it with the Skill tool; read its `references/style-dna.md`, `xiaohei-ip.md`, `object-patterns.md`, `master-selection.md` and `qa-checklist.md` as that skill directs. |
| `references/pipeline.md` | When a build fails, or you need a CLI flag, config key or cost answer. |

Read `script-writing.md` in full, from the file — not from memory of a previous run. They are the accumulated repairs for reels that shipped wrong, and they get edited between runs. A run that skips them reproduces the exact failures they describe.

## Step 1 — Pick the idea and name the lesson

Read `list.md`. Each idea is a block: `- [ ] **Day N — Title**` followed by `Hook:`, a body paragraph, `Angle:`, `Visual:`, `End on:`. The whole block is the brief. Take the **first unchecked** block unless the user named a topic — then use theirs, and append it to `list.md` as an unchecked entry if it is missing so the build can tick it off.

**The block is a seed, not a spec.** It was written fast, in bulk, months before this reel. Its Hook, Angle, Visual and End on are one person's first guess — they exist to say *which* idea and *why it deserves a reel*. Nothing in them is binding. Do not paste them into beats. If a better hook, order or ending exists, that is what ships.

Then write one plain sentence — no wordplay — stating what a viewer knows after watching that they did not know before. It goes in the json as `lesson`. The pipeline ignores the key; every later decision is graded against it.

> lesson: A storm on Jupiter never dies because there is no land under it to break it apart.

Not `The Great Red Spot is big and old` — that is a fact, and a viewer can already recite it and still learn nothing.

Do **not** tick the idea off. The build does that itself, keyed off the rendered mp4, so a failed build leaves the idea available for retry.

## Step 2 — Draft `scripts/<slug>.json`

Slug: kebab of the Day title + a 2-digit counter — Day 1 "Why we only have 8 planets" → `8-planets-01`. Bump the counter if the file exists.

Copy `style`, `image` and `voice` **from `scripts/8-planets-01.json`**, not from whatever is newest. That file is the reference reel for everything except the look. One change when copying: drop `voice.model` entirely so it falls through to the free tier in `src/reelkit/config.py`. Keep `voice.reference_id` — the voice is a brand asset and never changes.

Two things do **not** come from that file any more, because the handdrawn look is retired:

```json
"style_lock": "real photographic objects arranged in a clean white studio, one clear main object with unified soft light and perspective, light contact shadows only, a small simple black cartoon character carrying out the one core physical action, two to four short handwritten labels, four to six small colour accents in blue pink yellow green or red, generous breathing space around every object",
"image": { "palette": [{ "name": "clean white", "hex": "#FFFFFF" }] }
```

Paste both verbatim into every new script. The lock is the xiaohei style DNA compressed into one comma-separated English clause; `Script.load` refuses a script whose prompt has a reworded copy. The palette is one tone because the skill's white studio is non-negotiable — the old six-tone rotation was a property of the retired paper look, and `paper_for` wraps a single-entry palette onto every beat without complaint.

Scripts rendered before this switch (`8-planets-01` through `flat-plane-01`) keep their old handdrawn lock and their six-tone palette. Do not retro-fit them; their mp4s are already out. New reels use the block above.

Write the file with these keys:

| Key | What |
|---|---|
| `topic` | The Day title, verbatim — `plan.py` matches it against `list.md` to tick the idea off |
| `lesson` | The sentence from Step 1 |
| `slug` | As above |
| `music` | `null` unless the user asks |
| `prompt_format` | `"full"` — every prompt is complete and goes to the image model untouched |
| `subject_anchor` | One line naming what the reel is about, in objects: `"the solar system and the people who study it: planets, moons, orbits, telescopes, star charts, observatories and the night sky"`. Required. It governs the reel, not every frame |
| `style_lock` | The xiaohei clause above, verbatim. Never reworded, never per-reel flourishes — reel 40 has to look like reel 20 |
| `beats` | 6–12 of them, each `{id, text, scene}` |
| `post` | Written in Step 4 |

**Do not write a follow/subscribe beat.** `script.load` appends `DEFAULT_OUTRO` — same line, same red-button frame, every reel. Writing your own doubles it.

### Beat fields at draft time

```json
{ "id": "05", "text": "So nothing ever slows the spin, and the storm just keeps turning.",
  "scene": "close overhead on the huge oval storm turning between two cloud belts, fine filaments being wound into it, one thin whorl escaping off the trailing edge" }
```

- `text` — one spoken sentence, the narration. Rules in `references/script-writing.md`.
- `scene` — part 2 of the prompt contract and the **only** part you write by hand. 15–30 words: white studio, one real main object, 小黑 mid-action on it, one small prop, generous space. No style words; style is the lock. Derive it with `ian-xiaohei-scenes` — Step 3.
- `image_text` (optional) — literal words to letter into this one frame, **English**, 1–3 words. Two or three beats per reel at most.
- `anchored: false` + `grounded` (optional) — for a beat deliberately about the everyday case the subject violates. `grounded` names what to leave out, e.g. `"contains no planet, telescope or other space object"`.

`image_prompt` is not written by hand. Step 3 generates it.

## Step 3 — Expand scenes into full prompts

Invoke the `ian-xiaohei-scenes` skill and follow it as written — its master lock (§2B), its variation budget, its object rules and its QA checklist are the house look now. Do the master lock in your head or in the reply; it does not go in the json.

Four deltas, and only four, because this repo ships vertical English reels and that skill ships 16:9 Chinese article art. Everything else in it applies verbatim:

| Skill says | Here |
|---|---|
| 16:9 landscape, or 2.6:1 long scroll | **9:16 vertical, 1152×2048.** The long-scroll 彩蛋 mode never applies — there is no such frame in a reel |
| 2–4 short **Chinese** handwritten labels | **English**, 1–3 words, and only on the 2–3 beats that carry `image_text`. Everything else gets the no-text rule, because narration is English and a Chinese label argues with the voice |
| shot list of 4–8 standalone images | one frame per beat, 6–12, reading as one sequence — `subject_anchor` keeps the column on topic |
| generate, QA the candidate, regenerate | `reel.py` renders; QA by looking at `assets/<slug>/` after the build and re-rolling failures with `--only` |

Compose each beat's `scene` to that, then run:

```bash
python3 .claude/skills/make-reel/scripts/expand_prompts.py scripts/<slug>.json
```

It reads each `scene` and writes the finished `image_prompt`: canvas line, scene, anchor clause, `style_lock` verbatim, the studio-white background line, text rule, avoid line. Doing it in code rather than by hand is deliberate — the pasted lock, the background and the text rule are mechanical, and every one of them is something `Script.load` rejects the whole script for. Re-run it any time you edit a `scene`; it is idempotent.

Then review what it produced, because the script can only check form, not judgement:

- **True to its own line, first.** A viewer with sound on must see the sentence they are hearing. Nothing is added to a frame to keep it "on topic" — that is how a beat about ordinary Earth storms ends up with a model of Jupiter on the windowsill, which reads as a mistake to everyone who sees it.
- **On topic across the column.** Someone scrubbing with the sound off should be able to name the subject from the pictures. That is a property of the whole reel, satisfied by writing beats about the subject — never by bolting the subject onto a frame where it does not belong.
- **Separation.** No two neighbouring frames repeating an object class or a 小黑 pose. The paper tones used to do this work; on one white background it is the objects or nothing.
- **One action, one object.** The skill's budget, and it holds here: one core physical action, one main object, 1–2 small props, ≤4 labels. Listing every noun in the beat is the failure it names 元素清单化.

## Step 4 — Write the `post` block

A rendered mp4 is not postable. `post` is read by the build, which writes `assets/<slug>/post.txt` and the cover.

Watch the namespace: `post.caption` is the description beside the reel. `style.caption_*` are the subtitles burned into the picture. Different things.

```json
"post": {
  "caption": "<hook restated flat>\n\n<follow line>\n\n#reels #trending #viral #explorepage #reelsinstagram #jupiter #greatredspot #space #astronomy #science",
  "thumbnail_beat": "01"
}
```

- `caption` — the entire feed description exactly as it will be pasted, in three blocks separated by blank lines: 1–2 sentences restating the hook plainly (someone reading with the sound off decides from this alone), then the follow prompt, then the tags on their own last line. Never paste the narration; it reads as a transcript.
- **Hashtags** — inline in that last line, **10 maximum**, and these five are always among them:

  ```
  #reels #trending #viral #explorepage #reelsinstagram
  ```

  They are the reach tags and never change between reels. Spend the remaining five or fewer on this reel specifically — `#jupiter`, `#greatredspot`, `#astronomy` — because the fixed five are pure competition and the specific ones are how anyone actually finds you. Past 10 the tail is noise; past 30 the apps silently drop them and `post.py` warns.
- `thumbnail_beat` — the cover. Default `"01"`, the hook. Pick another only when a later frame is stronger with no narration behind it.

## Step 5 — Build

```bash
python3 reel.py build scripts/<slug>.json --no-captions
```

Images, narration, stitch, cover and post text, then it ticks the idea off `list.md` itself.

`--no-captions` is required on this machine: its ffmpeg has no libass, so burned-in subtitles cannot render. The `.ass` file is still written to `build/<slug>/`. If `ffmpeg -hide_banner -filters | grep ' ass '` ever matches, drop the flag — burned-in captions measurably help retention on muted autoplay.

When it fails, go to `references/pipeline.md` before changing anything. The two common failures have specific fixes and neither is "rewrite the json":

- **Script rejected at load** — the message names the beat and the missing clause. Fix the `scene`, re-run `expand_prompts.py`.
- **Some images failed** — what rendered is kept and paid for. Re-run only the failures with `python3 reel.py images scripts/<slug>.json --only 03,07`, then `build` again.

Never tick the idea off by hand while a build is broken.

## Step 6 — Verify, then report

1. The mp4 exists at the printed path, size > 0.
2. `out/<slug>-thumb.jpg` and `assets/<slug>/post.txt` exist.
3. The build printed `ticked off in list.md`. If it printed `! no unchecked list.md entry matches ...`, the `topic` does not match any open entry — say so, and do not hand-edit `list.md`.
4. Report: idea, slug, beat count, mp4 path, cover path, and the post text inline so it can be pasted without opening a file.

Different cover without re-rendering: `python3 reel.py thumb scripts/<slug>.json --beat 07`. `assets/<slug>/thumbs/contact.jpg` shows every candidate at once — offer it when the hook frame is weak.

If any step was skipped or unverified, say which. A reported success you did not actually see is worse than a reported gap.

## One look, no side paths

`ian-xiaohei-scenes` is the only image style this repo has. There is no photoreal path and no handdrawn path — both were removed on purpose, and a request for either is a request to change every reel at once. Say that rather than quietly rendering one frame off-style.

Everything in a frame is English: narration, subtitles, `image_text`. That is the one place this repo overrides the skill, and it is not per-reel discretion.
