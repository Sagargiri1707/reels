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
- `beats`: 6–12 beats, written to the storytelling rules below. **Do not write a follow/subscribe beat** — the build appends the standard sign-off itself (`DEFAULT_OUTRO` in `src/reelkit/config.py`): same spoken line, same mascot-slams-a-red-button frame, every reel. Writing your own would double it.
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

**Every prompt is the same three slots in the same order**, so twelve frames read as one set:

```
<ONE REAL OBJECT, named with its material>, <the mascot's single physical action on it>, <one detail showing the action mid-happening>
```

> `a chrome desk fan running at full speed`, `the mascot gripping its wire guard with both arms`, `and streaming out sideways like a flag`

Name the material — "a brass egg timer" renders as a photograph, "a timer" renders as an icon. Say what the mascot grips; a mascot holding nothing reads as standing nearby. Pick the object family for the whole reel before writing any beats, so the objects feel like they came out of one cupboard.

- **One real object, one mascot action.** The frame is a real object photographed on white, with the small mascot physically doing the thing the beat is about. Simple and explanatory, readable in a second.
- **The mascot carries the idea.** Delete it from the frame in your head — if the idea still reads, rewrite the frame. Standing beside the object or pointing at it is a failure.
- **Every beat must look different from the beat before it.** Two similar-looking frames in a row read as a stall and get swiped. Change the object, the camera distance, or what the mascot is doing.
- **Pick the concrete object, not the abstraction.** "Trust" isn't an object; "an unsigned contract the mascot is pinning down" is. If a beat is conceptual, find the object that stands in for it.
- **Each prompt renders independently.** No "the same object as before", no "the other side of the room". Restate the object in full every time.
- Structure: **the real object → what the mascot is doing to it → one small detail.** 15–30 words. No style words, no background colour, no lettering unless the beat opts in via `image_text` (Step 3).
- Full rules, including the character definition and the white-studio composition, in `references/visual-style.md`.

## Before writing the file, check

- Read beat 1 and the last beat back to back. Do they form a question and its answer? If not, fix the hook or the payoff — don't paper over it in the middle.
- Delete any beat the viewer wouldn't miss. 7 tight beats beat 11 loose ones.
- Check each adjacent pair for _but/so_ logic, not _and then_.
- Scan the image prompts as a column. Any two neighbors that would render alike get rewritten.

## Step 3 — Refine every prompt against the visual style

**Read `references/visual-style.md` in this skill directory. Not optional, not skippable, and not something to do from memory — read the file.** It is the house look: photoreal objects on white, with one small hand-drawn mascot doing something to them.

It is built on the `ian-xiaohei-scenes` skill, vendored in this repo at `.claude/skills/ian-xiaohei-scenes/`. Read that skill's `references/xiaohei-ip.md` and `references/style-dna.md` for the character and composition rules, and look at its `assets/examples/` — those are the quality bar. Do **not** let it generate anything; `reel.py` owns image generation, and its 16:9 Chinese-label defaults are overridden in `visual-style.md`.

Then do two passes over the json:

1. **`style_lock`** — copy the canonical string verbatim from the "The two halves" section of `references/visual-style.md`. That file is the source of truth, not the older scripts; `glass-rain-01` and `8-planets-01` predate it and are not being re-rendered. Do not reword it or add per-reel flourishes. Reel 40 has to look like reel 1. If it genuinely must change, change it in `visual-style.md` and say so in the final report.
2. **Every `image_prompt`** — rewrite it in full against the whole of `visual-style.md`, not just its checklist. Each prompt is judged on:
   - **The delete test.** The mascot performs the beat's core physical action. Remove it from the frame; if the idea still reads completely, the frame has failed. Standing beside the object, pointing at it, or watching it are all failures.
   - **One object, one action.** One real main object plus at most one or two small accessories. Readable in about a second at scroll speed. No diagrams, no panel strips, no labelled process rows.
   - **On topic.** The anchor comes through the **main object itself** — a planet model, a star chart — not through scenery parked in the corner of every frame. Beats get written and rendered one at a time, so each frame drifts into illustrating its own sentence; twelve beats about Pluto once came back as a dictionary, a broom and a kitchen table. Someone scrubbing with the sound off must be able to name the topic from the pictures alone.
   - **Relatability.** A familiar everyday object, scale shown by comparison rather than by number, consequence rather than mechanism. The narration explains how it works; the frame shows what it does to someone.
   - **Separation.** No two neighbouring frames sharing an object type and a camera distance.

Hard constraints:

- **English only.** No Chinese characters anywhere in a prompt.
- Prompts are scene-only. No style words — style lives in `style_lock`, and the pipeline appends it (`Script.prompt_for`).
- Never write "no text" into a prompt or into `style_lock`. `prompt_for` appends the text rule automatically, per beat.
- Never name a background colour in a prompt. The white studio is part of `style_lock`. `image.palette` still exists for tinted-paper reels but is off by default — the mascot style needs clean white.
- Portrait 9:16. Compose tall; a wide row of items renders thin and small. The source skill composes for 16:9, so say the vertical arrangement out loud.

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
