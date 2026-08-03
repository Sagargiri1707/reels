# Design reference

Everything the renderer already decides, and the small set of things the spec can
still say. Read this before writing a spec.

## Contents

- [Palette](#palette)
- [Canvas and safe box](#canvas-and-safe-box)
- [Tiers and sizing](#tiers-and-sizing)
- [Placement](#placement)
- [Highlight markup](#highlight-markup)
- [Spec schema — carousel](#spec-schema--carousel)
- [Spec schema — reel](#spec-schema--reel)
- [Audio](#audio)
- [Failure modes](#failure-modes)

## Palette

Six backgrounds. Each one comes with a fixed ink and a fixed accent — the spec
chooses only the background, because ink contrast is a legibility constraint and
not a design opinion.

| `color` | Background | Ink | Accent |
|---|---|---|---|
| `lavender` | `#D5BCFE` | `#33435F` slate navy | `#0B3E89` royal blue |
| `royal-blue` | `#0B3E89` | `#FFFFFF` | `#EFB143` mustard |
| `slate-navy` | `#33435F` | `#FFFFFF` | `#EFB143` mustard |
| `warm-beige` | `#E6C6A1` | `#33435F` | `#E32434` red |
| `mustard` | `#EFB143` | `#33435F` | `#0B3E89` royal blue |
| `red` | `#E32434` | `#FFFFFF` | `#E6C6A1` warm beige |

All ink pairings clear 5:1 against their background. The accents clear 4.5:1
except beige-on-red, which is around 3:1 — that one is fine because the accent
only ever carries one or two words of large bold display type, where 3:1 is the
accessible bar, but it is the one pairing not to use for a whole line.

One background per post. A carousel that changes colour between slides reads as
a mistake, not as variety; the variety comes from placement and from the words.

Rotate colours across posts. Check the last few:

```bash
grep -h '"color"' scripts/motivation/*.json | tail -8
```

## Canvas and safe box

| | Carousel | Reel |
|---|---|---|
| Size | 1080 × 1350 (4:5) | 1080 × 1920 (9:16) |
| Top margin | 130 | 300 |
| Bottom margin | 150 | 480 |
| Side margins | 100 | 110 |

The reel margins are much larger because Instagram draws its own chrome over the
frame — the caption, the audio strip, the action rail. Text inside the safe box
survives that; text outside it gets covered on somebody's phone.

Font is Comic Sans MS from `/System/Library/Fonts/Supplemental/`. Bold for hero
tier, regular for body. Line spacing is 1.28× the font size.

## Tiers and sizing

| Tier | Size range | Max lines | Default weight |
|---|---|---|---|
| `hero` | 78–132 px | 4 | bold |
| `body` | 54–96 px | 6 | regular |
| `kicker` | 40–66 px | 5 | regular |

Sizes are fitted, never specified. The renderer finds the largest size in the tier
that fits the safe box within the line cap, then — for a carousel — applies the
*smallest* fitted size in each tier to every slide in that tier. That is what makes
six slides read as one set instead of six unrelated images.

Slide 1 defaults to `hero`, the rest to `body`. Override with `"tier": "hero"` on
the closing slide, which usually earns it.

The line cap matters more than it looks: a hero line that wraps six times is a
paragraph in a big font, and it stops working at thumbnail size. When the cap
cannot be met the renderer falls back to fitting the box alone rather than
failing, so a long slide still renders — it just stops being a hero.

## Placement

Five vertical slots: `top`, `upper`, `center`, `lower`, `bottom`. Horizontal
alignment is per-post via `align` (`center` default, or `left` / `right`) and
stays the same across the whole carousel.

Leave `position` out and the renderer walks a fixed rotation seeded by the slug,
never repeating a neighbouring slide. Set it only for a slide with a specific
need. `"position": "auto"` is the same as leaving it out.

Note what stays constant while the slot moves: the margins, the alignment, and
the font size. That is the "in sync" part — the text lands somewhere different on
each slide but always inside the same frame, so swiping feels like one object
moving rather than five layouts.

## Highlight markup

Square brackets mark accent-coloured runs:

```
"You are not [behind]."
"The real spread is [decades] wide."
```

The brackets are markup and never render. One highlight per slide; two only when
the sentence has two genuine turns. Three highlights is the same as none.

## Spec schema — carousel

`scripts/motivation/day-NN-carousel.json`

```json
{
  "day": 1,
  "type": "carousel",
  "slug": "not-behind",
  "topic": "Day 1 — carousel — You are not behind, you are just early",
  "color": "slate-navy",
  "align": "center",
  "slides": [
    { "text": "You are not [behind].", "tier": "hero" },
    { "text": "You are measuring yourself against a schedule nobody wrote down." },
    { "text": "Line one.\nLine two.", "position": "lower", "bold": true }
  ],
  "caption": "…\n\n…\n\n#reels #trending …"
}
```

| Key | Required | Notes |
|---|---|---|
| `day` | yes | Integer. Decides the output folder `out/motivation/day-NN/` |
| `type` | yes | `carousel` |
| `slug` | yes | kebab-case, names the files and seeds the placement rotation |
| `topic` | yes | The list-motivation.md title **verbatim** — this is how the tick works |
| `color` | yes | One of the six palette keys |
| `align` | no | `center` (default), `left`, `right` |
| `slides` | yes | 4–8 of them |
| `slides[].text` | yes | `\n` forces a line break; `[word]` highlights |
| `slides[].tier` | no | `hero` on slide 1, `body` after |
| `slides[].position` | no | Leave out — see [Placement](#placement) |
| `slides[].bold` | no | Defaults to true for `hero`, false otherwise |
| `caption` | no | Written to `post.txt`. Omitting it warns |

Output: `out/motivation/day-NN/carousel/<slug>-01.png` … plus `post.txt`.

## Spec schema — reel

`scripts/motivation/day-NN-reel.json`

```json
{
  "day": 1,
  "type": "reel",
  "slug": "two-minute-version",
  "topic": "Day 1 — reel — The two-minute version",
  "color": "mustard",
  "text": "You don't need [motivation].\nYou need a smaller first step.",
  "duration": 11,
  "caption": "…"
}
```

Same shared keys, plus:

| Key | Required | Notes |
|---|---|---|
| `text` | yes | The whole reel. One thought |
| `duration` | no | Seconds, default 11. Audio fades in and out over 1.5s |
| `position` | no | `center` default — a still reel has no reason to sit off-centre |
| `tier` / `bold` / `align` | no | `hero`, bold, centred |
| `audio` | no | Repo-relative path to pin one track |

Output: `out/motivation/day-NN/reel/<slug>.mp4`, the `<slug>-frame.png` it was
built from, and `post.txt`. H.264 / yuv420p / 30fps, AAC 128k.

## Audio

`assets/motivation-audio/` holds every candidate track. The renderer picks one
deterministically from the slug, so the same reel keeps the same pad across
re-renders while different reels get different ones.

`make_pads.py` writes four synthetic pads there — slow, low, quiet chords with a
soft tremolo. They are placeholders: drop real mp3/m4a/wav files into the folder
and they join the rotation immediately, and delete the generated ones once you
have tracks you actually like.

With the folder empty and no `audio` key, the reel renders silent rather than
failing. That is deliberate — a silent mp4 is a fixable problem, a dead build is
not.

## Failure modes

**"does not fit even at Npx"** — the text is longer than the format holds. Cut
it. Lowering the tier floor to make it fit produces a slide nobody reads while
scrolling, which is worse than a shorter slide.

**"nothing unchecked matches"** — `topic` does not match a `- [ ]` line in
`list-motivation.md`. Fix `topic` in the spec rather than editing the plan.

**Ugly line breaks** — the wrapper is greedy and does not know about phrases.
Force the break with `\n` in the text.

**A carousel where every slide looks the same** — usually every slide is the same
tier *and* the same length. Vary the sentence lengths; the placement rotation
handles the rest.
