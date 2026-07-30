# Visual style

The house look for every reel in this repo: **photoreal objects on a white
studio background, with one small hand-drawn mascot doing something to them.**

It comes from the `ian-xiaohei-scenes` skill, vendored at
`.claude/skills/ian-xiaohei-scenes/`. Read its `references/xiaohei-ip.md` and
`references/style-dna.md` when you need the source of truth on the character or
the composition. `assets/examples/` there are the quality bar — look at them
before writing prompts. Do not let that skill generate anything; `reel.py` owns
image generation.

Its defaults are Chinese 16:9 article illustrations. The overrides for this
repo are in "What we change" below, and they are not negotiable per-reel.

## The two halves

**Realistic half.** Real objects, rendered like studio product photography: a
laptop, a broom, a balance scale, a paper chart. Correct materials, correct
weight, one consistent soft light, a light contact shadow under each object.
Never a flat vector icon, never a drawing of the object.

**Anime half.** One small mascot, drawn flat over the photograph:

- solid black bean or capsule body, roughly 1.5:1 to 2.2:1 tall
- two small white dot eyes
- thin stick arms and legs
- slightly irregular hand-drawn outline
- calm, deadpan, blank expression — no mouth, or one minimal line
- no clothing, no props to explain who it is
- about 8–13% of the frame height, never the giant main subject

It is not a cute mascot and not a children's cartoon. No big shiny eyes, no
smile, no emoji face. Its charm comes from doing an absurd thing seriously.

## The mascot must carry the action

This is the rule that makes or breaks a frame. The mascot performs the beat's
core physical action — it is not standing beside the object looking at it.

> **The delete test.** Remove the mascot from the frame. If the idea still
> reads completely, the frame has failed. Rewrite it.

Good: straining to hold a name plaque on as the last screw drops. Wedging a
tenth planet into a full shelf. Sweeping rocks off a track. Rubbing out a word
with an eraser twice its size.

Bad: standing in the corner. Pointing at the object. Holding up a sign.
Watching something happen. Posing next to it.

## One object, one action

Each frame is **one real main object** (or one tight cluster that reads as one),
plus at most one or two small accessories — a paperclip, a binder clip, a sticky
note, a length of tape. Plus the mascot, mid-action.

Simple and explanatory, not busy. The frame should be readable in about a
second at scroll speed. If a beat needs three objects to make sense, it is
three beats, or it is one object chosen better.

Do not build a diagram, a flowchart, a process strip or a labelled panel set.
The previous version of this file allowed stacked panels; it produced cluttered
frames and is gone.

## Background and colour

- Background is clean white, near `#FFFFFF`. Not warm white, not grey, not
  beige, no gradient, no vignette, no paper texture, no room around it.
- Shadows are light contact shadows under objects only. They never spread into
  a grey background.
- Colour is accent only: blue tape, pink tape, yellow sticky, small green dot,
  red underline for a pain point. Four to six small touches per frame, no more.
  Large colour areas make it look cheap.
- The mascot's black and the object's real colours carry the frame.

## What we change from the source skill

| ian-xiaohei-scenes default | this repo |
|---|---|
| Chinese handwritten labels | English, and usually no words at all |
| 16:9 article illustration | 9:16 portrait, always |
| Long-scroll ultra-wide egg mode | never — one beat is one frame |
| Labels on tags, 2–4 per image | at most one short word, via `image_text` |
| Scene covers 60–72% of width | compose tall; leave the top and bottom open |

Portrait is the big one. The source composes wide, so state the vertical
arrangement explicitly: stack the object and the mascot, shoot from a low angle,
or let a tall object fill the height. A wide row renders thin and small.

## The subject anchor

`subject_anchor` is one line naming what the whole reel is about, in objects:

> the solar system and the people who study it: planets, moons, orbits,
> telescopes, star charts, the night sky

`prompt_for` welds it onto every prompt, so no frame drifts off the subject.
Required — the loader refuses a script without one.

It exists because beats are written and rendered one at a time, so each frame
drifts into illustrating its own sentence. Twelve beats about Pluto once came
back as a dictionary, a broom, a signpost and a kitchen table: every frame
defensible alone, and a reel that read as being about stationery. Someone
scrubbing with the sound off must be able to name the topic from the pictures.

**Anchor through the main object, not through scenery.** Make the real object
itself belong to the subject — a planet model, a star chart, a telescope. Do
not satisfy the anchor by parking a small observatory in the corner of every
frame; that reads as a repeated watermark and it is a mistake this repo has
already made once.

## Text in the frame

Default is no text. `prompt_for` appends the no-text rule automatically, so
never write "no text" into an `image_prompt` or into `style_lock`.

A beat opts in with `image_text`, holding the literal words only. Two or three
beats in a twelve-beat reel at most. Every rendered word is a chance for
garbled lettering, which is the most obviously-AI thing a frame can do.

Opt in only when the word is the payload of the beat, is genuinely undrawable,
is one or two words, and has a real surface to sit on — a plaque, a page, a
sticky note. Uppercase and plain. English only; never Chinese, whatever the
source skill's examples show.

## Writing a prompt

Structure: **the real object → what the mascot is doing to it → one small
detail.**

> a small grey rock on a white museum pedestal, the mascot straining with both
> arms to hold its name plaque on as the last screw drops away

Around 15–30 words. No style words — style lives in `style_lock`. No background
colour — that is handled for you. Every frame renders alone, so restate the
subject in full every time; never "the same object as before".

Give the viewer a way in: a familiar everyday object, scale shown by comparison
rather than by number, the consequence rather than the mechanism. The narration
explains how it works; the frame shows what it does to someone.

## Before you build

Scan the prompts as a column:

- Does every frame pass the delete test?
- Is any frame carrying more than one main object?
- Do any two neighbours share an object type and a camera distance?
- Does more than three beats carry `image_text`?
- Is anything drawn as a diagram or a panel strip instead of a real object?
- Is the anchor coming through the main object, or through corner scenery?
