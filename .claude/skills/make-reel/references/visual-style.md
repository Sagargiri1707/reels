# Visual style

The house look for every reel in this repo. Distilled from the ian handdrawn
technical-illustration system and adapted to what this pipeline actually is:
vertical 9:16 frames, one per spoken beat, English only.

Read this instead of invoking `ian-handdrawn-ppt`. That skill targets 16:9
Chinese slide decks with pastel fills and page furniture — roughly 80% of it
has to be overridden here, and overriding it at runtime is where the style
drifts. The usable parts are below.

## The lock

`style_lock` is one comma-separated English clause and it is the same string in
every script in this repo. Copy it verbatim from `scripts/8-planets-01.json`. Do
not reword it, do not "improve" it, do not add per-reel flourishes — the whole
point is that reel 40 looks like reel 1.

`glass-rain-01` and `venus-day-01` are the exception and must not be copied from.
They were built during a retired experiment that swapped this look for photoreal
objects on white with a drawn mascot; the reels stay, the lock does not.

It carries style and only style — no subject, no background colour, no text
rule. Scene goes in `image_prompt`, topic in `subject_anchor`, background in
`image.palette`, text per beat. The pipeline assembles the final prompt in
exactly one place, `Script.prompt_for` in `src/reelkit/script.py`.

If the lock genuinely needs to change, change it in every script at once and
say so — a silent one-off edit is the failure mode this file exists to prevent.

## The subject anchor

`subject_anchor` is one line naming what the whole reel is about, in objects:

> the solar system and the people who study it: planets, moons, orbits,
> telescopes, star charts, the night sky

`prompt_for` welds it onto every single prompt, so no frame can drift off the
subject. It is required — the loader refuses a script without one.

This exists because of a specific failure. Beats get written one at a time and
rendered one at a time, so each frame ends up illustrating its own sentence in
isolation. Do that across twelve beats about Pluto and you get a dictionary, a
broom, a signpost and a kitchen table — every frame defensible on its own, and
a reel that reads as being about stationery. Someone scrubbing the timeline with
the sound off must be able to name the topic from the pictures alone.

**The two-in-three rule.** At least two frames in every three contain a literal
object from the topic — the actual planet, the actual telescope, the actual
night sky. Metaphor is the exception you spend when the topic object genuinely
cannot carry the beat, and even then the anchor has to show up somewhere in the
frame: put the orrery on the desk next to the dictionary.

**Prefer the literal thing.** "Nine chalk planets on a classroom board, a tenth
added lower in a hesitant hand" beats "a signpost with two arms" for the same
beat. It carries the same idea and it stays on topic.

## Paper tones

`image.palette` is a list of muted paper colours; the beat's position picks one,
wrapping at the end. So neighbouring frames never share a background.

Twelve frames on one paper tone read as a single held image no matter how
different the drawings are — the cut has nothing to land against. Rotating the
paper is the cheapest variance in the pipeline and costs no prompt budget.

Do not name a colour inside an `image_prompt`; `prompt_for` appends the paper
clause. Every tone stays muted and light enough that ink still reads on top. If
you add tones, keep them adjacent in mood and far apart in hue, and never let
one go saturated — the ink has to stay the loudest thing on the page.

## What carries over from ian

- **Detailed ink and pencil, not doodle.** Fine varied line weight, real
  cross-hatching and stippling for shade, believable proportions and material
  texture. A rock should look like rock, cloth like cloth.
- **Object drawing over icon.** Draw the real thing with its construction
  details — a broom with bristles, a plate with a corner chipped — not a flat
  vector glyph of it.
- **Large negative space.** The subject sits small and calm in the frame. A
  filled canvas reads as cheap.
- **One idea per frame.** Two subjects maximum. If the beat needs three things
  to make sense, it is two beats.
- **Faint corner construction marks only.** Grid ticks, a stray ruler line.
  Incidental and very quiet. Never a border or full frame around the image.
- **No people unless the beat is about people.** At most one small figure, off
  to a side. Never a figure next to every element.
- **Props stay blank.** Books, screens, signs and papers carry no writing
  unless that beat opts into text. No fake English, no invented labels, no
  gibberish, no watermark.

## What does not carry over

| ian default | this repo |
|---|---|
| Simplified Chinese in the image | English, and usually nothing at all |
| 16:9 body page, 21:9 cover | 9:16 portrait, always |
| Pastel marker label fills | sparing muted washes, ink stays dominant |
| One fixed paper tone across a deck | a tone per beat, rotated |
| Page numbers, title block, underline | none — there is no page furniture |
| Deck of slides sharing a shell | independent frames sharing a lock |

## Framing for 9:16

The image config is portrait (`1152x2048`). Compose tall:

- Prefer subjects that stack vertically — a column, a falling thing, a figure,
  a tall object seen head-on — over ones that spread sideways.
- A row of items across the frame goes small and thin in portrait. If a beat
  needs a row, say so explicitly and keep it to three or four items.
- Say the vantage point out loud in the prompt: *seen from far above*, *from the
  very back of the room*, *close overhead*, *from a low angle*. This is the
  single most effective lever for making neighbouring frames look different.

## Text in the frame

Default is **no text**. `prompt_for` appends the no-text rule automatically, so
never write "no text" into an `image_prompt` or into `style_lock`.

A beat may opt in with the optional `image_text` field. Use it sparingly —
two or three beats in a twelve-beat reel, never most of them. Every rendered
word is a chance for the image model to produce garbled lettering, and garbled
lettering is the most obviously-AI thing a frame can do.

Opt in only when **all** of these hold:

1. The word is the payload of the beat, not decoration.
2. It is genuinely undrawable — a name, a label, a single number.
3. It is short: one or two words, ideally under 20 characters.
4. It has a natural surface to sit on — a plaque, a page, a chalkboard, a
   readout — not floating in space.

Good: an eraser rubbing out the word `PLANET`. A blank dictionary entry whose
headword is `PLANET`. A pedestal plaque reading `PLUTO`.

Bad: labelling all three panels of a diagram. Captioning what the narration
already said. A number that a drawn quantity would show better.

Keep it uppercase and plain. `prompt_for` handles the phrasing — the field
holds only the literal words.

## Writing a prompt

Structure each `image_prompt` as: **vantage point → subject → what the subject
is doing → one supporting detail.**

> a far overhead view of a wide ring of hundreds of tiny irregular ice
> fragments, one slightly larger round body drifting among them

No style words. No "the same man as before" — every frame renders alone, so
restate the subject in full every time.

## Depth: write the whole frame, not the noun

A one-noun prompt gets you a one-noun image floating in the middle of nothing.
Aim for 15–30 words carrying **three** specifics the model can act on. Cheap
adjectives do not count — "beautiful", "detailed", "amazing" change nothing.
These do:

- **Vantage and distance.** *from the very back of a lecture hall*, *close
  overhead*, *from a low angle looking up*.
- **A verb.** The subject should be mid-action, not posed. An eraser being
  *lifted*, a hand *still touching* the page, ice *drifting*. Frozen motion
  reads alive; a static object reads like clip art.
- **One imperfection.** Real things have wear. A chipped corner, a curled page
  edge, crumbs scattered, one bulb missing, a chair pushed out. This single
  detail is what separates a drawing from a stock icon.
- **A second plane.** Something small and quiet behind or beside the subject
  that implies a world continuing past the frame edge. Not clutter — one thing.

Stop before it becomes a paragraph. Four good specifics beat ten weak ones, and
past ~30 words the image model starts dropping whichever ones it likes least.

## Relatability: anchor it to the viewer's own life

The viewer will not feel a number. They feel a thing they have touched. Before
committing a prompt, ask: **where has this person seen this object before?**

- **Prefer the domestic and the everyday** over the institutional and the
  cosmic. A kitchen sink beats a laboratory. A classroom wall chart beats an
  observatory dome. A supermarket shelf beats a data centre.
- **Put a human trace in the frame even with no human in it.** A hand at the
  edge, a worn handle, a half-drunk mug, a chair still pushed back. It tells
  the viewer a person was here, which makes the idea feel like it happened to
  someone rather than to physics.
- **Scale by comparison, never by number.** The viewer cannot picture 143,000
  kilometres. They can picture a marble dropped into a swimming pool. Whenever
  a beat's line contains a big number, the frame's job is to make that number
  feel like an amount — put a familiar object beside it.
- **Show the consequence, not the mechanism.** The narration explains how it
  works. The frame shows who it lands on. If the line is about a storm that
  never stops, draw the same window on the same house, unchanged, across three
  generations of curtains — not a diagram of wind shear.
- **Everyday, not decorative.** The point is recognition, not charm. Avoid
  whimsy for its own sake — cute animals, mascots, smiling suns. They read as
  a children's book and cost the reel its credibility.

Test: if the frame would look equally at home in a textbook diagram and in
nobody's actual memory, rewrite it.

## Before you build

Scan the prompts as a column, ignoring the text:

- Do any two neighbours share a vantage point and a subject scale? Rewrite one.
- Is anything drawn that the narration already says out loud? Replace it with
  what the narration leaves out.
- Do more than three beats carry `image_text`? Cut back to the strongest.
- Is any beat trying to draw an abstraction? Find its physical stand-in.
