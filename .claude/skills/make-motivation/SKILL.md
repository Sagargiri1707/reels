---
name: make-motivation
description: Text-only motivation and self-help post factory for this repo — turns an idea from list-motivation.md into either an Instagram carousel (4–8 plain-background PNG slides, Comic Sans, one house colour) or a still reel (one text frame over a calm ambient pad, ~11s mp4), plus the caption. Use this whenever the user says "make a motivation post", "next motivation post", "make a carousel", "quote post", "self-help post", "motivational reel", "do day N", "next from list-motivation", or hands over a motivational/self-help line and wants it turned into a post. Also use for any single piece of one: rewriting slide copy, re-picking the colour, changing text placement, regenerating the background audio, re-rendering the mp4, or writing the caption and hashtags. If the request touches list-motivation.md, scripts/motivation/*.json, out/motivation/, the six-colour palette, Comic Sans slides or the ambient pads, this skill owns it — use it rather than improvising with PIL or ffmpeg by hand. This is the no-image-model path: nothing here calls fal or generates artwork. For the illustrated science reels with narration and 小黑 scenes, use `make-reel` instead.
---

# Make Motivation

One idea becomes either a carousel of text slides or an eleven-second text reel.

```
list-motivation.md idea → scripts/motivation/day-NN-<type>.json
                        → render_post.py → out/motivation/day-NN/<type>/
```

You author exactly one artefact: the spec json. Everything after it is one command.

Nothing here uses an image model. The whole look is a flat colour and Comic Sans,
which is a deliberate constraint — these posts win or lose on the sentence, and a
generated background is one more thing competing with the words for attention.

| File | When |
|---|---|
| `references/writing.md` | Before writing any slide or reel line. What separates a post someone saves from the fortune-cookie version. |
| `references/design.md` | Before touching the spec. Palette, tiers, placement, the full spec schema, failure modes. |

Read `writing.md` from the file each run, not from memory of the last one. It is
where the repairs accumulate.

## Step 1 — Pick the idea

Read `list-motivation.md`. Each block is:

```
- [ ] **Day 3 — carousel — Rest is part of the work**
      idea: ...
      angle: ...
      color: lavender
```

Take the **first unchecked** block unless the user names a topic — then use theirs
and append it to `list-motivation.md` as an unchecked entry so the render can tick
it off. The `type` in the title decides carousel or reel.

The block is a seed, not a script. `idea` and `angle` say *which* post and *why it
is worth making*; nothing in them is copy. If a sharper line exists, that is what
ships.

Do not tick the block off by hand — `render_post.py` does it, keyed off files that
actually exist, so a failed render leaves the idea available.

## Step 2 — Write the copy

Read `references/writing.md`, then write the slides or the reel line.

A **carousel** is 4–8 slides of one continuous thought. Slide 1 is the hook that
has to survive being seen at thumbnail size with no context. The middle slides are
the argument, one beat each. The last slide is the line worth screenshotting.
Someone should be able to swipe through with no sound and come out having changed
their mind about one small thing.

A **reel** is a single line held on screen for eleven seconds. If it needs a second
sentence to land, it is a carousel.

Highlight one or two words per slide by bracketing them — `You are not [behind].`
The brackets are markup and render as accent colour, not as characters. Use them
on the word the sentence turns on, and not on more than one word per slide; a
slide with three highlights has no emphasis at all.

## Step 3 — Write `scripts/motivation/day-NN-<type>.json`

Full schema and every field in `references/design.md`. The short version:

```json
{
  "day": 1,
  "type": "carousel",
  "slug": "not-behind",
  "topic": "Day 1 — carousel — You are not behind, you are just early",
  "color": "slate-navy",
  "slides": [
    { "text": "You are not [behind].", "tier": "hero" },
    { "text": "You are measuring yourself against a schedule nobody wrote down." }
  ],
  "caption": "..."
}
```

`topic` must be the list-motivation.md title verbatim — that string is how the
render finds the line to tick off.

**Colour is one flat background for the entire carousel.** Every slide the same,
because a carousel is one object and switching colour mid-swipe reads as a
mistake. Pick a colour the last three or four posts did not use:

```bash
grep -h '"color"' scripts/motivation/*.json | tail -8
```

Take `color` from the list block if it names one. The ink and accent are not
yours to choose — the renderer pairs them with the background, because contrast
is a legibility question and every free choice there is a chance to ship an
unreadable slide.

**Do not set `position` unless you have a reason.** Left out, the renderer varies
the vertical placement across the carousel from a fixed rotation and never repeats
a neighbour. That is the behaviour you want: identical placement on every slide
reads as a template, random placement reads as sloppy, and hand-picking five
positions is five chances to get it wrong. Set it only when one slide genuinely
needs to sit somewhere specific.

**Do not set font sizes.** There are none in the schema. The renderer fits each
tier and then uses one size for that tier across the whole carousel, so the set
reads as one piece rather than as six separately-designed images.

## Step 4 — Write the caption

`caption` is the feed description, pasted exactly as written, in three blocks
separated by blank lines:

1. One or two sentences restating the idea plainly. Not the slide copy — someone
   who already swiped is not reading it twice.
2. The follow line.
3. The hashtags, on their own last line, **10 maximum**.

These five are always in the tag line and never change:

```
#reels #trending #viral #explorepage #instagood
```

Spend the remaining five on this post — `#motivation`, `#selfimprovement`,
`#discipline`, `#mindset`, `#habits`. The fixed five are pure competition; the
specific ones are how anyone finds you. Past 10 the tail is noise.

## Step 5 — Render

```bash
python3 .claude/skills/make-motivation/scripts/render_post.py scripts/motivation/day-01-carousel.json
```

Slides or mp4, `post.txt`, and the tick in `list-motivation.md`, all from that one
command. Add `--no-tick` when re-rendering something already shipped.

The reel picks a pad from `assets/motivation-audio/` deterministically from the
slug, so a re-render keeps its own track. Any mp3/m4a/wav dropped in that folder
joins the rotation; the generated pads are placeholders and can be deleted once
real tracks exist. To regenerate them:

```bash
python3 .claude/skills/make-motivation/scripts/make_pads.py
```

Pin a specific track with `"audio": "assets/motivation-audio/pad-e-minor.mp3"` in
the spec.

When it fails, the message names the slide. The two real failures:

- **"does not fit even at Npx"** — the text is too long, and the fix is to cut it,
  not to shrink the floor. A slide nobody can read while scrolling is not a slide.
- **"nothing unchecked matches"** — `topic` does not match a `- [ ]` line in
  `list-motivation.md`. Fix `topic`; do not hand-edit the plan.

## Step 6 — Look at it, then report

Actually open the PNGs. The renderer can check that text fits inside a box; it
cannot see that a line broke in an ugly place, that the highlighted word was the
wrong one, or that slide 4 says the same thing as slide 3.

Check:

1. Every file exists and is non-zero. For a reel, `ffprobe` shows the expected
   duration and an audio stream.
2. Read the slides in order as a stranger would. Does slide 1 make anyone stop?
   Does the last one earn a screenshot? Is any middle slide restating its neighbour?
3. The line breaks. A hero slide that breaks mid-phrase reads badly even when the
   words are right — insert an explicit `\n` in the text to control the break.
4. `post.txt` exists and the tag line has ten or fewer tags.
5. The render printed `ticked off in list-motivation.md`.

Report: the idea, the slug, slide count or duration, the output folder, and the
caption inline so it can be pasted without opening a file. If a step was skipped
or unverified, say which — a reported success nobody looked at is worse than a
reported gap.

## One look, no side paths

Six colours, Comic Sans, flat background, no imagery. That is the whole visual
system and it is what makes fifty posts look like one account. A request for a
gradient, a photo, a generated background or a second typeface is a request to
change every post at once — say so rather than quietly shipping one post
off-style.
