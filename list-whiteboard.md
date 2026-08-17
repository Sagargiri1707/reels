# Whiteboard Animation Queue

One image per line. `- [ ]` = todo, `- [x]` = mp4 rendered.
Paste an image URL (or a local path). Nothing else required.

```

```

The `srt-whiteboard-animation` skill does the rest. Optional note after `—` steers
region order, timing, or ink style; leave it off and the defaults apply.

---

## What happens per item

Image-URL input has no SRT, so steps 1–2 of the skill (subtitle strategy + line-art
generation) are skipped. Narrative order comes from the picture itself.

1. **Fetch** — download to `assets/whiteboard/<slug>/scene-01-<slug>.png`, read real pixel W×H.
2. **Annotate** — look at the image, split it into subjects, write
   `scene-01-<slug>.annotation.json`: integer-pixel `region` per element, `sequence` in
   drawing order (scene setting → main subject → action/change → result), `subtitle` left
   empty, overlaps guarded with `protectedRegions`. `canvas` must equal the source pixels.
3. **Time it** — no subtitles to time against, so each region's `durationMs` ≈
   draw distance ÷ 150 px/s, regions serial (no `startMs` overlap, +200ms breath between),
   `sceneDurationMs` = last region end + 0.5s hold.
4. **Check** — render the numbered region preview and show it. **One confirm gate here.**
   Fix-ups go through `assets/preview.html` (drag regions, reorder, retime, save back).
5. **Render** — `render_stream_whiteboard.py` → `scene-01-<slug>-whiteboard.mp4`.
6. **Tick the box** here once the mp4 exists.

Multiple images in one item (`url1, url2`) render as scenes 01, 02, … then merge with
`merge_scenes.py` into `<slug>-final.mp4`.

## Defaults

| Thing    | Default                                                                        |
| -------- | ------------------------------------------------------------------------------ |
| Paper    | warm cream `#F5EBD7`, sampled from the source image corners — never pure white |
| Ink path | `--ink-path grid`; say "skeleton" in the note for clean line art               |
| Colour   | `--color-fill contour-wipe`; `brush` on request                                |
| Weights  | ink : color = 2 : 1 per region                                                 |
| Ending   | at least 0.5s of the full, finished image                                      |

Source images should be simple line art on a light background — a busy photo has no clean
strokes to trace and the pen path turns to mush. If the URL is a photo, say so before rendering.

## Commands

```bash
python .claude/skills/srt-whiteboard-animation/scripts/prepare_env.py   # first run only, prints ENV_PY=
```

```bash
python .claude/skills/srt-whiteboard-animation/scripts/render_annotation_preview.py <img> <ann> <preview.png>
```

```bash
<ENV_PY> .claude/skills/srt-whiteboard-animation/scripts/render_stream_whiteboard.py <img> <ann> <out.mp4> .claude/skills/srt-whiteboard-animation/assets/drawing-hand.png
```

Note: `out/` and `*.mp4` are gitignored, so rendered videos stay local.

---

## Queue

<!-- add items below -->

- [x] https://i.pinimg.com/474x/c3/5d/b0/c35db0b6f752ff0128ecbd7ace48b247.jpg
- [x] https://i.pinimg.com/474x/29/de/a7/29dea7c0c694059274ded5b5508b780d.jpg
- [x] https://i.pinimg.com/474x/68/cf/d2/68cfd22a193f992f98e8864bc470be68.jpg
- [x] https://i.pinimg.com/474x/66/16/3d/66163d1a889af344ba96deeff448d49a.jpg
- [x] https://i.pinimg.com/474x/dd/6f/2b/dd6f2b3892598fb24eec695a39720de2.jpg
- [x] https://i.pinimg.com/474x/70/ad/a9/70ada9184ec7919f107ebf82fa2a4e40.jpg
- [x] https://i.pinimg.com/474x/7d/2e/a6/7d2ea6282d08bb481a401fb8ce55c2c1.jpg
- [x] https://i.pinimg.com/474x/63/9c/e6/639ce6ad569f612c9c766494053af827.jpg
- [x] https://i.pinimg.com/474x/5d/c2/1b/5dc21b330fc6209270337046db69ba59.jpg
- [x] https://i.pinimg.com/474x/fe/46/21/fe4621dc60d848dd3f1a4e6d29ca3ce3.jpg
- [x] https://i.pinimg.com/474x/2e/e0/e9/2ee0e98cc039b1fa5751772597161b81.jpg
- [x] https://i.pinimg.com/474x/92/1c/80/921c802baca4f6f0739bd083047c1edc.jpg
- [x] https://i.pinimg.com/474x/7f/41/8c/7f418c1b9c375e0146fb8eb5ddcfee53.jpg
- [x] https://i.pinimg.com/474x/13/70/fd/1370fd63ade24652337907e2749a76a3.jpg
- [x] https://i.pinimg.com/474x/ad/46/cc/ad46cc0c6ca0737f82c9f728367fa6e3.jpg
- [x] https://i.pinimg.com/474x/26/ab/43/26ab43c76cab219ff677081faf52a245.jpg
- [x] https://i.pinimg.com/474x/a3/c9/d2/a3c9d2e548521df5b4684d99bf826b24.jpg
- [x] https://i.pinimg.com/474x/19/13/1d/19131dd7641bcf4b94fe5d247ed20947.jpg
- [x] https://i.pinimg.com/474x/b9/5c/05/b95c05bc2ec73f354748b980778419ed.jpg
- [x] https://i.pinimg.com/474x/4b/84/8a/4b848a6c69177a4afa161edd402baae1.jpg
- [x] https://i.pinimg.com/474x/31/5a/9c/315a9c7faac987b5c5e2e6305ae1a199.jpg
- [x] https://i.pinimg.com/474x/0f/b2/d8/0fb2d8c72bb63b9ed6c32d7aef2af2ff.jpg
- [x] https://i.pinimg.com/474x/33/3c/38/333c38b70a8e50c2c3cf365b13e63732.jpg
- [x] https://i.pinimg.com/474x/21/16/79/21167985309ef9075d3226e44318aa1b.jpg
- [x] https://i.pinimg.com/474x/1e/19/01/1e19017a42dfa20e80587fa096948fda.jpg
- [x] https://i.pinimg.com/474x/05/b2/9b/05b29b6465c98edb1f3fc29e2b582ad0.jpg
- [x] https://i.pinimg.com/474x/f7/ad/7f/f7ad7f2af4f93f3379b8a9fe8df9cd47.jpg
- [x] https://i.pinimg.com/474x/50/1a/28/501a28db3dd8089c4f182c19d1637093.jpg
- [x] https://i.pinimg.com/474x/d7/53/35/d75335183856c5ce1d6fb2de9c681da4.jpg
- [x] https://i.pinimg.com/474x/80/16/36/80163638696f363abf3e42b2df86ddbf.jpg
- [x] https://i.pinimg.com/474x/92/1c/80/921c802baca4f6f0739bd083047c1edc.jpg
- [x] https://i.pinimg.com/474x/7f/41/8c/7f418c1b9c375e0146fb8eb5ddcfee53.jpg
- [x] https://i.pinimg.com/474x/13/70/fd/1370fd63ade24652337907e2749a76a3.jpg
