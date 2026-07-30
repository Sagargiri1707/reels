---
name: make-reel
description: End-to-end reel factory for this repo. Picks the next unchecked video idea from list.md, writes a scripts/<slug>.json, refines every image_prompt against the house visual style, builds the final mp4 with reel.py, picks a cover frame, writes the feed caption, and checks the idea off. Use whenever the user says "make a reel", "next reel", "build a video", "new reel from the list", "generate the next idea", or asks to turn an idea into a finished reel — even if they name a specific topic instead of using the list. Also use when they want a caption, hashtags or a thumbnail/cover for an existing reel.
---

# Make Reel

Turn one idea into a finished mp4: pick idea → write script.json → refine image prompts against `references/visual-style.md` → build with reel.py → mark idea done.

## Step 1 — Pick the idea

Read `list.md` in the repo root. Each idea is a block: a `- [ ] **Day N — Title**` heading followed by `Hook:`, a body paragraph, `Angle:`, `Visual:`, and `End on:` lines — that whole block is the brief for the reel, not just the title. Take the **first unchecked** block, unless the user named a specific topic — then use theirs (append it to list.md as an unchecked entry if missing, so it gets checked off at the end).

Treat the block as raw material, not a script to copy verbatim: the Hook is your hook beat's seed, Angle tells you the surprising reframe to build toward, Visual gives image-prompt direction per idea (not per beat), and End on is the payoff line to land on — but write fresh `text`/`image_prompt` beats per the Story shape and Writing rules below rather than pasting these lines directly into beats.

Do **not** mark it `[x]` yet. It only gets checked after the mp4 actually renders — a failed build should leave the idea available for retry.

## Step 2 — Write scripts/<slug>.json

Slug format: short kebab version of the Day title + 2-digit counter, e.g. Day 1 "Why we only have 8 planets" → `8-planets-01`. Bump the counter if the file exists.

Copy the structural config (`style`, `image`, `voice`) from the most recently committed script in `scripts/` — those settings are tuned and working; don't invent new values. Then write:

- `topic`: the Day title (e.g. "Why we only have 8 planets")
- `slug`: as above
- `music`: null unless user asks
- `beats`: 6–12 beats, written to the storytelling rules below. **Do not write a follow/subscribe beat** — the build appends the standard sign-off itself (`DEFAULT_OUTRO` in `src/reelkit/config.py`): same spoken line, same red-button frame, every reel. Writing your own would double it.
- `subject_anchor`: one line naming what the reel is about, in objects — e.g. `"the solar system and the people who study it: planets, moons, orbits, telescopes, star charts, the night sky"`. Required; the loader refuses a script without one. It rides on every image prompt so no frame drifts off topic.
- `style_lock`: leave a placeholder for now; Step 3 replaces it.
- `post`: the feed caption and cover-frame choice — written in Step 4.

## Beat schema

Each beat has:

- `text`: one spoken sentence — this becomes the narration
- `image_prompt`: a **scene-only** description (what is drawn, not how it's styled). Style comes from `style_lock` — the pipeline assembles the final prompt as `image_prompt + ", " + style_lock + ", " + text rule` (see `Script.prompt_for` in `src/reelkit/script.py`), so any style words in the beat prompt would fight the lock.
- `image_text` (optional): the literal words to letter into this one frame. Omit it and the frame renders with no writing at all, which is the default. See Step 3 before using it.

## Story shape

The beat list is not a list of facts. It's one story with a question at the front and its answer at the back. Lay it out like this:

1. **Hook** (beat 1) — opens a loop. A specific, concrete claim or question the viewer can't resolve on their own.
2. **Ground it** (beat 2) — the ordinary situation the hook violates, so the viewer knows what's at stake.
3. **Escalate** (middle beats) — each beat raises the tension or deepens the strangeness. One new idea per beat.
4. **Turn** (second-to-last) — the reveal that reframes everything before it.
5. **Payoff** (last beat) — closes the exact loop beat 1 opened. Not a summary, not a CTA.

**Chain beats causally, not sequentially.** Connect each beat to the last with _but_, _so_, _which is why_ — never _and then_. Test: if you can swap two adjacent beats and nothing breaks, the chain is weak and the viewer will leave in the gap. Rewrite so beat N only makes sense because beat N-1 happened.

**Re-hook every third beat.** Attention decays. Around beats 4 and 7, plant a fresh micro-question — "but that's not the strange part", "and nobody could explain why" — so there's always an unanswered thing pulling the viewer forward.

**Pay off what you promised.** Whatever beat 1 implies, the last beat must deliver. A hook the script doesn't cash is the fastest way to train viewers to skip you.

## Writing the `text` line

- One idea per sentence. If it contains "and", check whether it's two beats.
- Short. Aim under 18 words, one clause. It's spoken, not read — read it aloud before you keep it.
- Concrete over abstract. One vivid number, name, or sensory detail beats three adjectives.
- Second person where it fits. Put the viewer inside the scene rather than describing it to them.
- Written for TTS: no parentheses, no semicolons, no symbols or abbreviations the voice will mangle. Spell out anything ambiguous.
- Never open with a greeting, "did you know", "in this video", or "let's dive in". Beat 1 starts mid-momentum.

**Hook examples**

Weak: `The ocean is full of mysteries.` — a category, not a claim. Nothing to resolve.
Strong: `There's a patch of the Pacific where the nearest human is in orbit above you.`

Weak: `Sleep is really important for your brain.` — the viewer already agrees, so there's no loop.
Strong: `Your brain physically shrinks every night, and that's the point.`

## Writing the `image_prompt` line

The visuals carry retention as much as the words do.

- **Every beat must look different from the beat before it.** Two similar-looking frames in a row read as a stall and get swiped. Change the subject, the scale, or the vantage point.
- **Vary shot scale on purpose**: wide establishing → medium → close detail → back out. Eight wides in a row is a slideshow.
- **Draw the concrete noun, not the abstraction.** "Trust" isn't drawable; "two hands over an unsigned contract" is. If a beat is conceptual, find its physical stand-in.
- **Add, don't echo.** The image should show something the narration doesn't say. If the line is "the engine failed at 30,000 feet", don't draw a failing engine — draw the passengers' faces.
- **Each prompt renders independently.** No "the same man as before", no "the other side of the room". Restate the subject in full every time.
- One or two subjects max, scene-only — no style words. Frames carry no lettering unless the beat opts in via `image_text` (Step 3).
- **Write the whole frame, not the noun.** 15–30 words, with a vantage point, the subject mid-action, one imperfection, and one quiet second plane. A bare noun renders as clip art.
- **Anchor it to something the viewer has touched.** Domestic over institutional, a human trace even with nobody in frame, scale shown by comparison rather than by number. Full rules in `references/visual-style.md`.

## Before writing the file, check

- Read beat 1 and the last beat back to back. Do they form a question and its answer? If not, fix the hook or the payoff — don't paper over it in the middle.
- Delete any beat the viewer wouldn't miss. 7 tight beats beat 11 loose ones.
- Check each adjacent pair for _but/so_ logic, not _and then_.
- Scan the image prompts as a column. Any two neighbors that would render alike get rewritten.

## Step 3 — Refine every prompt against the visual style

**Read `references/visual-style.md` in this skill directory. Not optional, not skippable, and not something to do from memory — read the file.** It is the house look, distilled from the ian handdrawn technical-illustration system and already adapted to this pipeline.

Do **not** invoke the `ian-handdrawn-ppt` skill. It targets 16:9 Chinese slide decks with pastel fills and page furniture; roughly 80% of it has to be overridden here, and overriding it at runtime is exactly where the style drifts. Everything usable from it is in `visual-style.md`.

Then do two passes over the json:

1. **`style_lock`** — copy it verbatim from `8-planets-01.json`. Do not reword it or add per-reel flourishes. **Do not copy the lock from `glass-rain-01.json` or `venus-day-01.json`** — those two were built during a retired photoreal-object-and-mascot experiment and carry a lock that is no longer the house look. Reel 40 has to look like reel 1. If it genuinely must change, change it in every script at once and say so in the final report.
2. **Every `image_prompt`** — rewrite it in full against the whole of `visual-style.md`, not just its checklist. Each prompt is judged on:
   - **On topic.** At least two frames in every three contain a literal object from the reel's subject. Metaphor is the exception you spend when the topic object genuinely can't carry the beat — and even then the subject has to appear somewhere in the frame. **This is the failure mode to watch for**: beats get written and rendered one at a time, so each frame drifts into illustrating its own sentence, and twelve beats about Pluto come back as a dictionary, a broom and a kitchen table. Someone scrubbing with the sound off must be able to name the topic from the pictures alone.
   - **Depth.** 15–30 words carrying real specifics: vantage and distance, a verb putting the subject mid-action, one imperfection, one quiet second plane. A bare noun renders as clip art.
   - **Relatability.** Give the viewer a way in — a human trace in the frame even with nobody in it, scale shown by comparison rather than by number, consequence rather than mechanism. Do this *inside* the subject's world, not by leaving it.
   - **Separation.** No two neighbouring frames sharing a vantage point and a subject scale.

Hard constraints:

- **English only.** No Chinese characters anywhere in a prompt.
- Prompts are scene-only. No style words — style lives in `style_lock`, and the pipeline appends it (`Script.prompt_for`).
- Never write "no text" into a prompt or into `style_lock`. `prompt_for` appends the text rule automatically, per beat.
- Never name a background colour in a prompt. `image.palette` rotates a paper tone per beat and `prompt_for` appends it.
- Portrait 9:16. Compose tall; a wide row of items renders thin and small.

### Text inside a frame

Default is no text. A beat opts in with the optional `image_text` field, holding the literal words only:

```json
{ "id": "01", "text": "...", "image_prompt": "...", "image_text": "PLUTO" }
```

Use it on **two or three beats at most**, never on most of them — every rendered word is a chance for garbled lettering, which is the most obviously-AI thing a frame can do. Opt in only when the word is the payload of the beat, is genuinely undrawable, is one or two words, and has a real surface to sit on: a plaque, a page, a chalkboard, a readout. `visual-style.md` has the full rule and worked examples.

## Step 4 — Write the `post` block

A rendered mp4 still isn't postable. Add a `post` block to the json — the build reads it and writes `assets/<slug>/post.txt` plus the cover frame.

Careful with the name: `post.caption` is the description that sits **beside** the reel in the feed. The `style.caption_*` keys are the subtitles burned into the picture — different thing, don't cross them.

```json
"post": {
  "caption": "<hook restated flat>\n\n<follow line>\n\n#topic #science #...",
  "thumbnail_beat": "01"
}
```

- `caption`: the entire feed description, exactly as it will be pasted — there is no separate hashtag field. Write it in three blocks separated by blank lines: 1–2 sentences restating the hook plainly (someone reading with sound off decides from this line alone), then the follow prompt, then the tags on their own last line. Don't paste the narration; it reads as a transcript.
- **Hashtags** go inline in that last line, each with its own `#`. Use 8–12. Mix broad (`#science`, `#space`) with specific (`#spacetime`, `#venus`) — the broad ones are pure competition, the specific ones are how anyone actually finds you. Over 30 gets silently dropped by the apps, and the build warns if you cross it.
- `thumbnail_beat`: which beat becomes the cover. Default `"01"` (the hook). Pick a different beat only when a later frame is visually stronger on its own — the cover is judged with no narration behind it.

## Step 5 — Build

```bash
python3 reel.py build scripts/<slug>.json --no-captions
```

This renders the mp4, extracts one cover candidate per beat, and writes the post text — the last two are local ffmpeg and cost nothing.

`--no-captions` is required on this machine: its ffmpeg is built without libass, so burned-in subtitles can't render (the `.ass` file is still written to `build/<slug>/`, so they can be muxed in later). If `ffmpeg -hide_banner -filters | grep ' ass '` ever returns a match, drop the flag — burned-in captions measurably help retention on muted autoplay.

If the build fails, read the error, fix the json (common: schema validation in `src/reelkit/script.py`), and retry. Do not check off the idea while the build is broken.

## Step 6 — Verify and mark done

1. Confirm the mp4 exists at the path the build printed (check file size > 0).
2. Confirm `out/<slug>-thumb.jpg` and `assets/<slug>/post.txt` exist.
3. **The build ticks the idea off `list.md` itself** — that is the `-- plan` line at the end of its output, handled by `src/reelkit/plan.py`. Do not edit `list.md` by hand. Read the build output: if it printed `! no unchecked list.md entry matches ...`, the topic did not match any open entry, so check whether the idea is worded differently in the plan and say so in the report.
4. Report to the user: idea, slug, beat count, mp4 path, cover path, and the post text itself so it can be pasted without opening a file.

To try a different cover without re-rendering: `python3 reel.py thumb scripts/<slug>.json --beat 07`. `assets/<slug>/thumbs/contact.jpg` shows every candidate at once — offer it when the hook frame is weak.

If anything was skipped or unverified (e.g. build succeeded but you couldn't confirm the file), say so explicitly — don't report success you didn't see.
