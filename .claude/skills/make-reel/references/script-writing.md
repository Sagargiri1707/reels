# Script writing

How the beats get written. Read this before drafting `beats` in Step 2.

Contents:

- [The lesson is the spine](#the-lesson-is-the-spine)
- [Story shape](#story-shape)
- [Writing the `text` line](#writing-the-text-line)
- [Hooks that work and hooks that do not](#hooks-that-work-and-hooks-that-do-not)
- [Before you save the file](#before-you-save-the-file)

## The lesson is the spine

One sentence, written before any beat, stating what the viewer knows afterwards that they did not know before. It lives in the json as `lesson` and the pipeline never reads it — it is there so the beats can be graded against something.

> A storm on Jupiter never dies because there is no land under it to break it apart.

A beat that does not set the lesson up, set up the thing it violates, deepen it, complicate it or pay it off is a beat that gets cut, however good the line reads.

This step exists to prevent one specific reel: correct facts in a pleasing order that teach nothing, because no single sentence in it was ever the point. The middle is where it happens — the lesson quietly becomes trivia around beat 5, and the viewer feels it as "nice video, no idea what it was about".

**The mechanism is the reel.** For a why-does-this-happen idea, the beat explaining *why* is the one the whole thing exists for. Give it room: usually its own beat, sometimes two — one for the cause, one for the consequence. Never bury it as a clause inside a scale beat. Numbers, records and superlatives decorate it; cut every number and the reel should still teach the lesson.

## Story shape

The beat list is one story with a question at the front and its answer at the back, not a list of facts.

1. **Hook** (beat 1) — opens a loop. A specific, concrete claim or question the viewer cannot resolve alone.
2. **Ground it** (beat 2) — the ordinary situation the hook violates, so the viewer knows what is at stake.
3. **Escalate** (middle) — each beat raises the tension or deepens the strangeness. One new idea per beat.
4. **Turn** (second to last) — the reveal that reframes everything before it.
5. **Payoff** (last) — closes the exact loop beat 1 opened. Not a summary, not a CTA. The sign-off beat is appended by the pipeline; do not write one.

**Chain causally, not sequentially.** Join beats with *but*, *so*, *which is why* — never *and then*. Test: swap two adjacent beats. If nothing breaks, the chain is weak and the viewer leaves in that gap. Beat N should only make sense because beat N-1 happened.

**Re-hook every third beat.** Attention decays. Around beats 4 and 7, plant a fresh micro-question — "but that is not the strange part", "and nobody could explain why" — so something unanswered is always pulling forward.

**Pay off what you promised.** Whatever beat 1 implies, the last beat delivers. An uncashed hook is the fastest way to train viewers to skip you.

## Writing the `text` line

- One idea per sentence. If it contains "and", check whether it is two beats.
- Short — under 18 words, one clause. It is spoken, not read. Say it out loud before keeping it.
- Concrete over abstract. One vivid number, name or sensory detail beats three adjectives.
- Second person where it fits. Put the viewer inside the scene rather than describing it to them.
- Written for TTS: no parentheses, no semicolons, no symbols or abbreviations the voice will mangle. Spell out anything ambiguous.
- Never open with a greeting, "did you know", "in this video" or "let's dive in". Beat 1 starts mid-momentum.

Narration length drives runtime. 6–12 beats at these lengths lands in the 30–60s the plan targets; `python3 reel.py timeline scripts/<slug>.json` prints the cut points after the voice exists, without rendering.

## Hooks that work and hooks that do not

Weak: `The ocean is full of mysteries.` — a category, not a claim. Nothing to resolve.
Strong: `There's a patch of the Pacific where the nearest human is in orbit above you.`

Weak: `Sleep is really important for your brain.` — the viewer already agrees, so there is no loop.
Strong: `Your brain physically shrinks every night, and that's the point.`

The pattern: a strong hook is a specific claim the viewer cannot verify or dismiss on their own, so the only way to resolve it is to keep watching.

## Before you save the file

- Say the `lesson` out loud, then read the beats. Does someone who watched this end up knowing that sentence? If they end up knowing five facts instead, the mechanism beat is missing or buried.
- Name what each beat does for the lesson. Any beat with no answer gets cut — it is a fact you found interesting, not a beat.
- Read beat 1 and the last beat back to back. Question and answer? If not, fix the hook or the payoff rather than papering over it in the middle.
- Delete any beat the viewer would not miss. Seven tight beats beat eleven loose ones.
- Check every adjacent pair for *but/so* logic, not *and then*.
- Read each `scene` beside its own `text`. Anything in the frame that the line does not contain, and that is there to keep the frame on topic, comes out.
- Scan the scenes as a column. Any two neighbours that would render alike get rewritten.
