# Writing reference

The design system is four decisions wide and the renderer makes all four. So the
post is the sentence. This file is about the sentence.

## The bar

Motivation is the most saturated category on the platform. Every generic line has
already been posted ten thousand times with better design than yours. The only
thing that survives that is **specificity** — a claim precise enough that someone
could disagree with it.

Test: could this appear on a mug? If yes, it is not a post.

| Mug | Post |
|---|---|
| Believe in yourself | You are not behind. You are measuring against a schedule nobody wrote down |
| Consistency is key | People who look disciplined cut the cost of starting until it fell below the cost of avoiding |
| Rest is productive | Tired work is expensive work. You pay for it twice — once doing it, once fixing it |
| Don't compare yourself | You saw four people your age do the thing. That became the average in your head |

The right-hand column is not more inspiring. It is more *specific*, which is why
someone screenshots it: it says something they had not already fully formed.

## Say the mechanism

The move that makes a post land is naming *why* the thing is true, not just
asserting it. "Motivation follows action" is an assertion. "Motivation shows up
after you start, so make starting small enough that it isn't a decision" is a
mechanism, and a mechanism is actionable.

Every carousel should be able to answer: what does the reader now understand that
they did not before? Write that sentence for yourself before writing slide 1. If
the answer is "that they should try harder", start over.

## Carousel shape

4–8 slides, one continuous thought. The shape that works:

1. **Hook.** Seen at thumbnail size, no context, sound off, mid-scroll. It has one
   job: make the thumb stop. Usually a flat contradiction of what the reader
   expects, stated in under eight words.
2. **Turn.** Name the thing they are actually doing wrong, or the assumption
   underneath it. This is where the post either has an idea or doesn't.
3–5. **The argument.** One beat per slide. Each slide moves; a slide that restates
   its neighbour is a slide to delete. Concrete over abstract — numbers, an
   example, a named situation.
6. **The line.** What someone screenshots. It should follow from the argument, not
   summarise it. A summary is the weakest possible ending.

Do not number the slides and do not write "swipe →". The format already tells
people it swipes, and both are the visual signature of a template account.

**Slide length target.** Aim for 2–3 lines at the fitted size, 4 as a hard
ceiling — even on a body slide the schema allows six for. A slide that reads
like a caption is a slide nobody absorbs mid-swipe. If a sentence needs a
fifth line, cut it; don't rely on the renderer shrinking the font to save it.

## Reel shape

One line. Eleven seconds. A reel is a carousel that only earned one slide — which
is not a downgrade, it is a different job: reach, not depth.

If it needs a second sentence to make sense, it is a carousel.

The strongest still-reel lines are the ones that work as a complete thought and
also make you want the explanation. `Nobody is thinking about it as long as you
are.` `You can start over on a Tuesday.` Nothing to add, and something to argue
with.

## Voice

Second person. Present tense. Short declaratives.

Write the way someone who has actually thought about this talks — not the way a
caption talks. That means:

- **No stacked adjectives.** "Real, lasting, genuine change" is one adjective's
  worth of meaning spread over three.
- **No em-dash-into-revelation rhythm on every slide.** Once per carousel at most.
- **No rhetorical questions as hooks.** "Ever feel like you're behind?" is filler
  in the one position that cannot afford filler.
- **No hedging.** "Maybe try to consider" — the reader came for a position.
- **No therapy-speak** unless the post is genuinely about that. "Hold space",
  "honour your journey", "you got this" all read as borrowed language.
- **No self-help cadence for its own sake.** Three-word fragments. Stacked like
  this. For emphasis. It is exhausting past two slides.

Contractions are fine and usually better. `don't` reads as a person; `do not`
reads as a brand.

## Highlights

One bracketed word per slide, on the word the sentence turns on:

```
You are not [behind].
The real spread is [decades] wide.
```

Highlighting the emotional word instead of the load-bearing one is the common
mistake — `You are [not] behind` emphasises the wrong half. Ask which word the
reader would stress reading it aloud.

## Line breaks

The wrapper is greedy and breaks wherever the line runs out. On hero slides that
often lands mid-phrase. Force it with `\n`:

```
"You don't need [motivation].\nYou need a smaller first step."
```

Break on the sense, not on the width — the reader hears the pause.

## The caption

Not the slides again. Someone reading the caption either has not swiped yet, in
which case it is a second hook, or has finished, in which case they want the part
that did not fit. Write the version for whichever is more useful for that post.

One or two sentences, then the follow line, then the tags. Never a transcript of
the slides.

## Before you render

Read the slides in order out loud. Three questions:

1. Does slide 1 make anyone stop?
2. Does any slide restate the one before it?
3. Would someone screenshot the last one?

Two out of three is a post worth rendering. One is a rewrite.
