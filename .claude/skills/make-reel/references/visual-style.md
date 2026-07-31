# Visual style

The house look for every reel in this repo: vertical 9:16 frames, one per spoken beat, English only. Distilled from the ian handdrawn technical-illustration system and already adapted to this pipeline.

Read this instead of invoking `ian-handdrawn-ppt`. That skill targets 16:9 Chinese slide decks with pastel fills and page furniture — roughly 80% of it has to be overridden here, and overriding it at runtime is where the style drifts.

Contents:

- [The lock](#the-lock)
- [The prompt contract](#the-prompt-contract)
- [The subject anchor](#the-subject-anchor)
- [Paper tones](#paper-tones)
- [Writing the scene](#writing-the-scene)
- [Depth: write the frame, not the noun](#depth-write-the-frame-not-the-noun)
- [Relatability: anchor it to the viewer's life](#relatability-anchor-it-to-the-viewers-life)
- [Framing for 9:16](#framing-for-916)
- [Text inside a frame](#text-inside-a-frame)
- [What carries over from ian, and what does not](#what-carries-over-from-ian-and-what-does-not)
- [Before you build](#before-you-build)

## The lock

`style_lock` is one comma-separated English clause, identical in every script in this repo. Copy it verbatim from `scripts/8-planets-01.json`. Do not reword it, do not improve it, do not add per-reel flourishes — the point is that reel 40 looks like reel 1.

`glass-rain-01` and `venus-day-01` are the exception and must not be copied from. They were built during a retired experiment that swapped this look for photoreal objects on white with a drawn mascot; the reels stay, the lock does not.

The lock carries style and only style — no subject, no background colour, no text rule. Topic lives in `subject_anchor`, background in `image.palette`, text per beat. It is pasted verbatim into every `image_prompt`, and `Script.load` refuses a script whose prompt has a reworded copy.

If the lock genuinely must change, change it in every script at once and say so in the report. A silent one-off edit is the failure this file exists to prevent.

## The prompt contract

Scripts are `"prompt_format": "full"`: every `image_prompt` is complete and self-contained, and goes to the image model **exactly as written**. Nothing is appended at render time.

The reason is debuggability. A frame that came back wrong is diagnosed by reading one string in the file, not by re-deriving what four code paths welded onto it.

The seven parts, in this order:

1. **Canvas.** `9:16 vertical portrait canvas, 1152x2048.` First, verbatim. The model follows prompt text over the size parameter — leave this out and it composes for landscape and the subject gets cropped away.
2. **Scene.** Vantage → subject mid-action → one imperfection → one quiet second plane. 15–30 words.
3. **Anchor**, in one of two forms. Most beats: `the scene belongs to <subject_anchor>, and must visibly read as part of it.` A beat deliberately about the everyday case takes the grounded form, which names what to leave out: `this is an ordinary everyday scene and contains no planet, telescope or other space object; it is the ordinary case the rest of the reel is measured against.`
4. **The lock**, verbatim.
5. **Paper.** `drawn on <name> paper, flat background colour <HEX>.` — the tone at `image.palette[beat index % palette length]`, counting authored beats from zero.
6. **Text rule.** Either `no text, no letters and no numbers anywhere in the image.` or, for a beat with `image_text`, a rule naming those exact words and forbidding all other writing.
7. **Avoid**, the same closing line on every beat of every reel:

   > Avoid: full-page border or frame, page number, title, caption, label, watermark, gibberish or invented text, gradients, drop shadows, neon or saturated colour, crowded composition, flat vector icon look, childish doodles, cute mascots, several people, corporate template look.

**You write part 2 and nothing else.** `scripts/expand_prompts.py` assembles all seven from the `scene` field, so the constants stay byte-identical across a reel and across reels — hand-assembly drifts one beat at a time, and every part it drops is something `Script.load` rejects the whole script for.

Worked example, one finished beat:

> 9:16 vertical portrait canvas, 1152x2048. A far overhead view of a wide ring of hundreds of tiny irregular ice fragments, one slightly larger round body drifting among them, a gap torn through one arc, a faint second ring beginning far below. the scene belongs to the solar system and the people who study it: planets, moons, orbits, telescopes, star charts, observatories and the night sky, and must visibly read as part of it. `<lock verbatim>`. drawn on pale slate blue paper, flat background colour #DFE4E9. no text, no letters and no numbers anywhere in the image. Avoid: `<avoid line>`.

`Script.load` names the beat and the missing clause when the lock, the canvas, the beat's own paper hex or a text rule is absent. That check is the contract, not a linting nicety — everything it catches is something the pipeline used to guarantee by appending it.

The older `assembled` mode, where `image_prompt` held a fragment and `Script.prompt_for` welded the rest on, still exists for the scripts already built on it and for the pipeline's sign-off beat. Do not write new scripts on it.

## The subject anchor

`subject_anchor` names what the whole reel is about, in objects:

> the solar system and the people who study it: planets, moons, orbits, telescopes, star charts, observatories and the night sky

Required — the loader refuses a script without one — and it governs the **reel**, not each individual frame.

It exists because of a specific failure. Beats get written one at a time and rendered one at a time, so each frame ends up illustrating its own sentence in isolation. Do that across twelve beats about Pluto and you get a dictionary, a broom, a signpost and a kitchen table: every frame defensible alone, and a reel that reads as being about stationery. Someone scrubbing with the sound off must be able to name the topic from the pictures.

**Two frames in every three carry a literal object from the topic** — the actual planet, the actual telescope, the actual night sky. That is a count over the column, satisfied by *writing beats about the subject*, never by decorating frames that are not.

**The frame's own line still wins.** When a beat is deliberately about something else — the ordinary Earth case, the comparison, the viewer's kitchen — the frame shows that thing cleanly, and the beat takes `anchored: false` plus a `grounded` clause naming what to leave out.

> Line: "Every storm you have ever sat through was gone within a week."
>
> Wrong: rain on a kitchen window, a chair blown over outside, **a cardboard model of Jupiter on the sill**. The viewer hears Earth, sees Jupiter, and spends the beat working out why the planet is there. It rendered exactly as asked and looked like a mistake.
>
> Right: rain on a kitchen window, a chair blown over outside, the puddles already drying at the edges. No planet anywhere. The reel earns its anchor on the ten frames that *are* about Jupiter.

If cutting the smuggled-in object would make a frame stop reading as part of the reel, the problem is the beat list, not the frame. Fix it upstream.

**Prefer the literal thing.** "Nine chalk planets on a classroom board, a tenth added lower in a hesitant hand" beats "a signpost with two arms" for the same beat: same idea, still on topic.

## Paper tones

`image.palette` is a list of muted paper colours and the beat's position picks one, wrapping — so neighbouring frames never share a background.

Twelve frames on one tone read as a single held image no matter how different the drawings are; the cut has nothing to land against. Rotating the paper is the cheapest variance in the pipeline and costs no prompt budget.

Exactly one colour is named per prompt — the paper clause and no other. Every tone stays muted and light enough that ink still reads on top. New tones stay adjacent in mood, far apart in hue, and never saturated: the ink has to remain the loudest thing on the page.

## Writing the scene

Part 2 of the contract, and the only part that changes between beats. Structure: **vantage point → subject → what the subject is doing → one supporting detail.**

> a far overhead view of a wide ring of hundreds of tiny irregular ice fragments, one slightly larger round body drifting among them

No style words here — style is part 4, pasted verbatim. No "the same man as before"; every frame renders alone, so restate the subject in full every time.

Two rules outrank everything else in this file:

- **The frame illustrates its own line.** A viewer with sound on must see the sentence they are hearing. A frame that argues with its narration is worse than a plain one — the viewer stops listening and starts working out what they are looking at.
- **Every beat looks different from the one before it.** Two similar frames in a row read as a stall and get swiped. Change the subject, the scale or the vantage point. Vary shot scale on purpose: wide establishing → medium → close detail → back out. Eight wides is a slideshow.

Then:

- **Draw the concrete noun, not the abstraction.** "Trust" is not drawable; "two hands over an unsigned contract" is. Every conceptual beat has a physical stand-in — find it.
- **Add detail, do not change subject.** The frame carries something the narration leaves out — who it happened to, what it left behind, what it cost — while staying unmistakably the same claim. "The engine failed at 30,000 feet" → the passengers' faces, yes; a different aircraft on a different day, no.
- **One or two subjects maximum.** If a beat needs three things to make sense, it is two beats.

## Depth: write the frame, not the noun

A one-noun prompt gets a one-noun image floating in the middle of nothing. Aim for 15–30 words carrying **three** specifics the model can act on. Cheap adjectives — "beautiful", "detailed", "amazing" — change nothing. These do:

- **Vantage and distance.** *from the very back of a lecture hall*, *close overhead*, *from a low angle looking up*.
- **A verb.** The subject mid-action, not posed: an eraser being *lifted*, a hand *still touching* the page, ice *drifting*. Frozen motion reads alive; a static object reads like clip art.
- **One imperfection.** A chipped corner, a curled page edge, crumbs, one bulb missing, a chair pushed out. This single detail separates a drawing from a stock icon.
- **A second plane.** One small quiet thing behind or beside the subject that implies a world continuing past the frame edge. Not clutter — one thing.

Stop before it becomes a paragraph. Four good specifics beat ten weak ones, and past ~30 words the image model starts dropping whichever it likes least.

## Relatability: anchor it to the viewer's life

The viewer will not feel a number. They feel a thing they have touched. Before committing a scene, ask: **where has this person seen this object before?**

- **Domestic over institutional and cosmic.** A kitchen sink beats a laboratory. A classroom wall chart beats an observatory dome. A supermarket shelf beats a data centre.
- **A human trace even with no human in frame.** A hand at the edge, a worn handle, a half-drunk mug, a chair still pushed back. It says a person was here, which makes the idea feel like it happened to someone rather than to physics.
- **Scale by comparison, never by number.** Nobody pictures 143,000 kilometres; everybody pictures a marble dropped into a swimming pool. When a line carries a big number, the frame's job is to make it feel like an amount.
- **Show the consequence, not the mechanism.** The narration explains how it works; the frame shows who it lands on. For a storm that never stops: the same window on the same house, unchanged, across three generations of curtains — not a diagram of wind shear.
- **Everyday, not decorative.** The point is recognition, not charm. Cute animals, mascots and smiling suns read as a children's book and cost the reel its credibility.

Do this inside whatever world the beat's own line is in — the subject's world for a subject beat, the viewer's kitchen for a grounding beat.

Test: if the frame would look equally at home in a textbook diagram and in nobody's actual memory, rewrite it.

## Framing for 9:16

The canvas is portrait, 1152x2048. Compose tall:

- Prefer subjects that stack vertically — a column, a falling thing, a figure, a tall object head-on — over ones that spread sideways.
- A row of items across the frame renders small and thin. If a beat needs a row, say so explicitly and keep it to three or four items.
- Say the vantage point out loud: *seen from far above*, *from the very back of the room*, *close overhead*, *from a low angle*. This is the single most effective lever for making neighbouring frames look different.

## Text inside a frame

Default is no text. A beat opts in with `image_text`, holding the literal words only, uppercase and plain:

```json
{ "id": "01", "text": "...", "scene": "...", "image_text": "PLUTO" }
```

Use it on **two or three beats at most**, never on most of them. Every rendered word is a chance for garbled lettering, which is the most obviously-AI thing a frame can do. `Script.load` caps the length and checks the words actually appear in the prompt — `image_text` is what the rest of the build believes is on screen.

Opt in only when **all** of these hold:

1. The word is the payload of the beat, not decoration.
2. It is genuinely undrawable — a name, a label, a single number.
3. It is one or two words, ideally under 20 characters.
4. It has a natural surface to sit on — a plaque, a page, a chalkboard, a readout — not floating in space.

Good: an eraser rubbing out the word `PLANET`. A blank dictionary entry whose headword is `PLANET`. A pedestal plaque reading `PLUTO`.

Bad: labelling all three panels of a diagram. Captioning what the narration already said. A number a drawn quantity would show better.

## What carries over from ian, and what does not

Carries over:

- **Detailed ink and pencil, not doodle.** Fine varied line weight, real cross-hatching and stippling for shade, believable proportions and material texture. Rock should look like rock, cloth like cloth.
- **Object drawing over icon.** The real thing with its construction details — a broom with bristles, a plate with a chipped corner — not a flat vector glyph.
- **Large negative space.** The subject sits small and calm. A filled canvas reads as cheap.
- **Faint corner construction marks only.** Grid ticks, a stray ruler line. Incidental and quiet. Never a border or full frame.
- **No people unless the beat is about people.** At most one small figure, off to a side.
- **Props stay blank.** Books, screens, signs and papers carry no writing unless the beat opts into text.

Does not:

| ian default | this repo |
|---|---|
| Simplified Chinese in the image | English, and usually nothing at all |
| 16:9 body page, 21:9 cover | 9:16 portrait, always |
| Pastel marker label fills | sparing muted washes, ink stays dominant |
| One fixed paper tone across a deck | a tone per beat, rotated |
| Page numbers, title block, underline | none — there is no page furniture |
| Deck of slides sharing a shell | independent frames sharing a lock |

## Before you build

Read each prompt beside its own `text` line:

- Would someone hearing the line recognise this frame as that line? If they would have to reconcile the two, the frame is wrong, not clever.
- Is anything in the frame there only to keep it on topic? Cut it.
- Is anything drawn that the narration already says out loud? Replace it with what the narration leaves out — inside the same claim, not a different one.

Then scan the prompts as a column, ignoring the text:

- Do any two neighbours share a vantage point and a subject scale? Rewrite one.
- Could someone name the reel's subject from the pictures alone? If not, the beats drifted; fix the beats.
- Do more than three beats carry `image_text`? Cut back to the strongest.
- Is any beat trying to draw an abstraction? Find its physical stand-in.
