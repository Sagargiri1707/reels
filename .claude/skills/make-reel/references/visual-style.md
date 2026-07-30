# Visual style

The house look for every reel in this repo: **photoreal objects on a white
studio background, with the owl mascot doing something to them.**

Two sources, and they cover different things:

- **The character** is `mascot.jpg` in this folder — the channel's own owl. It
  is the only authority on what the mascot looks like.
- **The composition** comes from the `ian-xiaohei-scenes` skill, vendored at
  `.claude/skills/ian-xiaohei-scenes/`. Read its `references/style-dna.md` and
  look at its `assets/examples/` for the object-on-white staging, the negative
  space and the quality bar. **Ignore its `references/xiaohei-ip.md` entirely** —
  that describes a deadpan black bean and explicitly forbids big eyes and
  smiles, which is exactly what our owl is. Do not let that skill generate
  anything; `reel.py` owns image generation.

Its defaults are Chinese 16:9 article illustrations. The overrides for this
repo are in "What we change" below, and they are not negotiable per-reel.

## The two halves

**Realistic half.** Real objects, shot like commercial product photography: a
laptop, a broom, a balance scale, a paper chart. It should look photographed,
not illustrated — sharp focus, visible surface texture, real reflections in
metal and glass, correct weight, one consistent softbox light, a light contact
shadow under each object. Never a flat vector icon, never a drawing of the
object, never a 3D render that looks like a render.

Naming the material in the prompt is what buys this. "a brass egg timer" gets a
photograph; "a timer" gets an icon.

**The canonical `style_lock`.** Copy this string verbatim into every new
script. It is the only place style is allowed to live:

```text
photorealistic macro product photograph of a real physical object on a clean seamless pure white #FFFFFF background, sharp focus and fine surface texture, true material detail with real reflections and micro scratches, physically accurate softbox studio lighting, only a light contact shadow beneath the object, no environment and no gradient; composited with one flat cel-shaded cartoon owl mascot standing in the scene at about one fifth of the frame height: round dark navy body with two pointed ear tufts, a large cream facial disc around both eyes, big round black eyes with golden yellow irises and a single white highlight, round thin wire-frame glasses, a small golden yellow beak open in a friendly smile, a golden yellow scalloped belly patch, navy wings with cream tips, yellow feet with small black claws, bold clean black outline and flat colour with no gradients; generous empty white space, vertical portrait composition
```

`glass-rain-01` and `8-planets-01` predate this string and are not being
re-rendered. They have the old black-bean mascot and a softer lock, so they will
not match anything built after them.

**Anime half.** One mascot: **a cartoon owl**, drawn flat over the photograph.

The reference is `mascot.jpg` in this folder. Look at it before writing prompts
and check every render against it. It cannot be sent to the image model —
`images.py` posts a prompt and nothing else — so the description below is the
only thing the model ever sees. Keep it word for word.

- round dark navy body, two pointed ear tufts
- large cream facial disc covering both eyes
- big round black eyes, golden yellow irises, one white highlight each
- round thin wire-frame glasses over both eyes
- small golden yellow beak, open in a small friendly smile
- golden yellow belly patch with scalloped feather lines
- navy wings with cream tips; yellow feet with small black claws
- bold clean black outline, flat cel-shaded colour, no gradients
- about a fifth of the frame height — present, but never the main subject

**It grips with its wings.** Write `with both wings`, `in one wing`, `in its
talons` — never "arms" or "hands". Prompts written before this mascot existed
say "both arms"; those reels are not being re-rendered.

**No quill.** The reference holds one; the owl in a reel needs its wings free
for the object. Only give it the quill when the beat is about writing.

It is a friendly scholar, not a deadpan blob — glasses, a small smile, and it
takes the absurd task seriously. That is the opposite of the character in
`ian-xiaohei-scenes`, whose rules explicitly forbid big eyes and smiles. Take
that skill's **composition** rules — real object on white, one action, the
delete test, negative space — and ignore its character definition entirely.

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
- Colour is accent only: blue tape, a small green or red dot, a length of
  masking tape. A few small touches per frame, no more. Large colour areas make
  it look cheap.
- The owl's navy and gold plus the object's real colours carry the frame. The
  mascot is already the brightest thing in it, so do not add a second accent
  colour competing with the gold.

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

## The pattern

Every prompt in every reel is the same four slots in the same order. Not a
suggestion — write them in this order every time, so twelve frames read as one
set instead of twelve separate ideas.

```
<ONE REAL OBJECT, named with its material>,
<the mascot's single physical action on it>,
<one physical detail that shows the action is happening>
```

Worked, from the reels in this repo:

| slot | example |
|---|---|
| object | `a chrome desk fan running at full speed` |
| action | `the owl gripping its wire guard with both wings` ||
| detail | `and streaming out sideways like a flag` |

| slot | example |
|---|---|
| object | `a ball of pale wool unravelling into one long trailing thread` |
| action | `the owl hauling back on the loose end with both wings` ||
| detail | `and losing` |

Rules for the slots:

1. **Object — name the material.** "a brass egg timer", "a chrome desk fan", "a
   grey rock cracked open". Material is what makes the render photoreal;
   "a timer" gets you a generic icon of a timer.
2. **Action — one verb, and say what the mascot grips.** `gripping with both
   wings`, `leaning its whole body against`, `hanging off with both wings`,
   `prying apart with a small crowbar`. A mascot with nothing to hold reads as
   standing nearby, which fails the delete test.
3. **Detail — show the action mid-happening.** The thread trailing, the last
   screw dropping, the fragments streaking past, the rock refusing to fit. This
   is the slot that stops the frame being a posed product shot.
4. **Length: 15–30 words.** Past that the model starts dropping slots.

Pick the object family before writing any beats. One reel's objects should feel
like they came out of the same cupboard — glassware and marbles and lab trays,
or timers and tools and workshop parts. Wandering across families beat to beat
is what made the frames look unrelated the first time round.

No style words — style lives in `style_lock`. No background colour — handled for
you. Every frame renders alone, so restate the object in full every time; never
"the same object as before".

Give the viewer a way in: a familiar everyday object, scale shown by comparison
rather than by number, the consequence rather than the mechanism. The narration
explains how it works; the frame shows what it does to someone.

## The sign-off

Every reel ends with the same beat, appended automatically by `script.load()`
from `DEFAULT_OUTRO` in `src/reelkit/config.py`. Spoken line, mascot slamming a
red push button, the word `FOLLOW` on it.

Do not write it into a script, do not reword it per reel, and do not add your
own closing beat on top of it. It is identical every time on purpose — that
repetition is the whole value, because a returning viewer should recognise the
ending before it finishes. It is also the one beat that skips the subject
anchor, so the button never turns into a space button.

A script can drop it with `"outro": false`, which is for one-offs that are not
going on the feed.

## Before you build

Scan the prompts as a column:

- Does every frame pass the delete test?
- Is any frame carrying more than one main object?
- Do any two neighbours share an object type and a camera distance?
- Does more than three beats carry `image_text`?
- Is anything drawn as a diagram or a panel strip instead of a real object?
- Is the anchor coming through the main object, or through corner scenery?
