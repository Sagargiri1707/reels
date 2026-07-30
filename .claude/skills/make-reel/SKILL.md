---
name: make-reel
description: End-to-end reel factory for this repo. Picks the next unchecked video idea from list.md, writes a scripts/<slug>.json, refines every image_prompt through the ian-handdrawn-ppt visual style, builds the final mp4 with reel.py, and checks the idea off. Use whenever the user says "make a reel", "next reel", "build a video", "new reel from the list", "generate the next idea", or asks to turn an idea into a finished reel — even if they name a specific topic instead of using the list.
---

# Make Reel

Turn one idea into a finished mp4: pick idea → write script.json → refine image prompts via ian-handdrawn-ppt → build with reel.py → mark idea done.

## Step 1 — Pick the idea

Read `list.md` in the repo root. Take the **first unchecked** item (`- [ ]`), unless the user named a specific topic — then use theirs (add it to list.md as unchecked if missing, so it gets checked off at the end).

Do **not** mark it `[x]` yet. It only gets checked after the mp4 actually renders — a failed build should leave the idea available for retry.

## Step 2 — Write scripts/<slug>.json

Slug format: short kebab topic + 2-digit counter, e.g. `sky-blue-01`. Bump the counter if the file exists.

Copy the structural config (`style`, `image`, `voice`) from the most recently committed script in `scripts/` — those settings are tuned and working; don't invent new values. Then write:

- `topic`: the idea text
- `slug`: as above
- `music`: null unless user asks
- `beats`: 6–12 beats. First beat is the hook (surprising claim or question), last is the payoff. Each beat:
  - `text`: one spoken sentence, conversational, short — this becomes the narration
  - `image_prompt`: a **scene-only** description (what is drawn, not how it's styled). Style comes from `style_lock` — the pipeline assembles the final prompt as `image_prompt + ", " + style_lock` (see `src/reelkit/script.py`), so any style words in the beat prompt would fight the lock.
- `style_lock`: leave a placeholder for now; Step 3 replaces it.

## Step 3 — Refine prompts with ian-handdrawn-ppt

Invoke the `ian-handdrawn-ppt` skill. Use it for **prompt crafting only** — read its `references/visual-dna-v6.md` and `references/prompt-patterns.md` and apply that visual system to this script. Do NOT let it generate images, pages, or decks; reel.py owns image generation.

Two outputs, both written back into the json:

1. **`style_lock`**: one comma-separated English style clause distilled from the ian visual DNA (handdrawn technical illustration feel, line quality, palette, paper background, composition rules). This is the single place style lives.
2. **Each `image_prompt`**: rewrite the scene description in the ian prompt-pattern voice — concrete drawable elements, clear focal subject, diagram-like clarity.

Hard constraints on the refined prompts:
- **English only. Any text that appears inside the image must be English.** The ian skill defaults to Chinese baked-in text — override that explicitly. No Chinese characters anywhere in the prompt.
- Keep prompts scene-only; style stays in `style_lock` (reason in Step 2).
- Keep vertical 9:16 framing in mind (the image config is portrait) — ignore the ian skill's 16:9/21:9 defaults.

## Step 4 — Build

```bash
python3 reel.py build scripts/<slug>.json --no-captions
```

If the build fails, read the error, fix the json (common: schema validation in `src/reelkit/script.py`), and retry. Do not check off the idea while the build is broken.

## Step 5 — Verify and mark done

1. Confirm the mp4 exists at the path the build printed (check file size > 0).
2. Flip the idea's `- [ ]` to `- [x]` in `list.md`.
3. Report to the user: idea, slug, beat count, mp4 path.

If anything was skipped or unverified (e.g. build succeeded but you couldn't confirm the file), say so explicitly — don't report success you didn't see.
