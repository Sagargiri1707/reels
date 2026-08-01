# Realistic image prompts

The house look in `visual-style.md` is handdrawn ink on paper. This file is the **other** path: when the ask is a realistic, photoreal, product, UI, logo or diagram image, not a reel frame.

**This path outputs a prompt and nothing else.** No `scripts/<slug>.json`, no `style_lock`, no `expand_prompts.py`, no `reel.py`. The deliverable is prompt text, printed in the reply, for the user to paste into whatever image model they are using later. Do not render, do not create files, do not tick anything off `list.md`.

Vendored from the OpenAI imagegen skill so it works offline — `skills/.system/imagegen/references/prompting.md` and `sample-prompts.md` in <https://github.com/openai/skills>. Execution controls from the original (`quality`, `input_fidelity`, masks, output paths, CLI flags) are dropped on purpose: they belong to that skill's renderer, and this path has no renderer.

Contents:

- [When this file applies](#when-this-file-applies)
- [Structure](#structure)
- [Specificity policy](#specificity-policy)
- [Allowed and disallowed augmentation](#allowed-and-disallowed-augmentation)
- [Composition and layout](#composition-and-layout)
- [Constraints and invariants](#constraints-and-invariants)
- [Text in images](#text-in-images)
- [Input images and references](#input-images-and-references)
- [Iterate deliberately](#iterate-deliberately)
- [Use-case tips](#use-case-tips)
- [Recipes — generate](#recipes--generate)
- [Recipes — asset templates](#recipes--asset-templates)
- [Recipes — edit](#recipes--edit)

## When this file applies

Use it when the user asks for a realistic / photorealistic / photoreal image, a product shot, a UI mockup, a wireframe, a logo, an infographic, a concept render, or an edit of an existing image — and does **not** want it in the reel style.

Do not use it for reel beats. A reel frame is `visual-style.md`'s seven-part contract with the lock pasted verbatim; mixing the two is how the house look drifts. If the user wants a realistic *reel*, that is a style change to every script at once — say so rather than doing it for one frame.

## Structure

- Consistent order: scene/backdrop → subject → key details → constraints → output intent.
- Include the intended use (ad, UI mock, infographic) — it sets the level of polish.
- For anything complex, use short labeled lines rather than one long paragraph. The recipes below are that format.

## Specificity policy

- If the user's prompt is already specific, **normalise it into a clean spec and add no creative requirements.**
- If it is generic, add tasteful detail where it materially improves the output.
- The recipes below are fully-authored examples, not the default amount of augmentation to bolt onto every request.

## Allowed and disallowed augmentation

Allowed on a generic prompt:

- composition and framing cues
- intended-use or polish-level hints
- practical layout guidance
- reasonable scene concreteness that supports the request

Never add:

- extra characters, props or objects that were not implied
- brand palettes, slogans or story beats that were not implied
- arbitrary left/right placement the surrounding layout does not support

## Composition and layout

- Specify framing and viewpoint (close-up, wide, top-down) and placement only when it materially helps.
- Call out negative space when the asset needs room for UI or copy.
- Avoid left/right layout decisions unless the user or the layout supports them.

## Constraints and invariants

- State what must not change: `keep background unchanged`.
- For edits: `change only X; keep Y unchanged`, and repeat the invariants on every iteration — that is what stops drift.

## Text in images

- Put literal text in quotes or ALL CAPS and specify typography: font style, size, colour, placement.
- Spell uncommon words letter-by-letter when accuracy matters.
- Require verbatim rendering and no extra characters.

## Input images and references

- Do not assume every supplied image is an edit target.
- Label each by index and role: `Image 1: edit target`, `Image 2: style reference`.
- Images given for style, composition or mood, with no request to modify them → generation with references.
- A request to preserve an existing image while changing specific parts → an edit.
- For compositing, describe how the images interact: `place the subject from Image 2 into Image 1`.

## Iterate deliberately

- Start from a clean base prompt, then make small single-change edits.
- Re-state the critical constraints on every iteration.
- One targeted follow-up at a time beats rewriting the whole prompt.

## Use-case tips

Generate:

- **photorealistic-natural** — prompt as if a real photo was captured in the moment; use photography language (lens, lighting, framing); call for real texture; avoid over-stylised polish unless asked.
- **product-mockup** — describe product, packaging and materials; clean silhouette, label clarity; in-image text verbatim with typography named.
- **ui-mockup** — state the fidelity first (shippable mockup or low-fi wireframe), then layout, hierarchy and practical UI elements. No concept-art language.
- **infographic-diagram** — define audience and layout flow; label parts explicitly; require verbatim text.
- **logo-brand** — simple and scalable; strong silhouette, balanced negative space; no decorative flourishes unless asked.
- **illustration-story** — define panels or scene beats; keep each action concrete.
- **stylized-concept** — style cues, material finish, rendering approach (3D, painterly, clay) without inventing story elements.
- **historical-scene** — state location and date, require period accuracy, constrain clothing, props and environment to the era.

Edit:

- **text-localization** — change only the text; preserve layout, typography, spacing, hierarchy; no extra words, no reflow unless needed.
- **identity-preserve** — lock face, body, pose, hair, expression; change only the named elements; match lighting and shadows.
- **precise-object-edit** — say exactly what is removed or replaced; preserve surrounding texture and lighting; everything else unchanged.
- **lighting-weather** — change only light, shadow, atmosphere, precipitation; keep geometry, framing and subject identity.
- **background-extraction** — clean cutout, crisp silhouette, no halos, label text preserved exactly, no restyling.
- **style-transfer** — name the style cues to preserve (palette, texture, brushwork) and what must change; add `no extra elements`.
- **compositing** — reference inputs by index; say what moves where; match lighting, perspective and scale; base framing unchanged.
- **sketch-to-render** — preserve layout, proportions and perspective; pick materials and lighting that support the sketch without adding elements.

## Recipes — generate

### photorealistic-natural

```
Use case: photorealistic-natural
Primary request: candid photo of an elderly sailor on a small fishing boat adjusting a net
Scene/backdrop: coastal water with soft haze
Subject: weathered skin with wrinkles and sun texture
Style/medium: photorealistic candid photo
Composition/framing: medium close-up, eye-level
Lighting/mood: soft coastal daylight, shallow depth of field, subtle film grain
Materials/textures: real skin texture, worn fabric, salt-worn wood
Constraints: natural color balance; no heavy retouching; no glamorization; no watermark
Avoid: studio polish; staged look
```

### product-mockup

```
Use case: product-mockup
Primary request: premium product photo of a matte black shampoo bottle with a minimal label
Scene/backdrop: clean studio gradient from light gray to white
Subject: single bottle centered with subtle reflection
Style/medium: premium product photography
Composition/framing: centered, slight three-quarter angle, generous padding
Lighting/mood: softbox lighting, clean highlights, controlled shadows
Materials/textures: matte plastic, crisp label printing
Constraints: no logos or trademarks; no watermark
```

### ui-mockup

```
Use case: ui-mockup
Primary request: mobile app home screen for a local farmers market with vendors and daily specials
Asset type: mobile app screen
Style/medium: realistic product UI, not concept art
Composition/framing: clean vertical mobile layout with clear hierarchy
Constraints: practical layout, clear typography, no logos or trademarks, no watermark
```

### infographic-diagram

```
Use case: infographic-diagram
Primary request: detailed infographic of an automatic coffee machine flow
Scene/backdrop: clean, light neutral background
Subject: bean hopper -> grinder -> brew group -> boiler -> water tank -> drip tray
Style/medium: clean vector-like infographic with clear callouts and arrows
Composition/framing: vertical poster layout, top-to-bottom flow
Text (verbatim): "Bean Hopper", "Grinder", "Brew Group", "Boiler", "Water Tank", "Drip Tray"
Constraints: clear labels, strong contrast, no logos or trademarks, no watermark
```

### logo-brand

```
Use case: logo-brand
Primary request: original logo for "Field & Flour", a local bakery
Style/medium: vector logo mark; flat colors; minimal
Composition/framing: single centered logo on a plain background with generous padding
Constraints: strong silhouette, balanced negative space; original design only; no gradients unless essential; no trademarks; no watermark
```

### illustration-story

```
Use case: illustration-story
Primary request: 4-panel comic about a pet left alone at home
Scene/backdrop: cozy living room across panels
Subject: pet reacting to the owner leaving, then relaxing, then returning to a composed pose
Style/medium: comic illustration with clear panels
Composition/framing: 4 equal-sized vertical panels, readable actions per panel
Constraints: no text; no logos or trademarks; no watermark
```

### stylized-concept

```
Use case: stylized-concept
Primary request: cavernous hangar interior with tall support beams and drifting fog
Scene/backdrop: industrial hangar interior, deep scale, light haze
Subject: compact shuttle parked near the center
Style/medium: cinematic concept art, industrial realism
Composition/framing: wide-angle, low-angle
Lighting/mood: volumetric light rays cutting through fog
Constraints: no logos or trademarks; no watermark
```

### historical-scene

```
Use case: historical-scene
Primary request: outdoor crowd scene in Bethel, New York on August 16, 1969
Scene/backdrop: open field with period-appropriate staging
Subject: crowd in period-accurate clothing, authentic environment
Style/medium: photorealistic photo
Composition/framing: wide shot, eye-level
Constraints: period-accurate details; no modern objects; no logos or trademarks; no watermark
```

## Recipes — asset templates

The labeled lines are prompt scaffolding, not a closed schema. Drop any line the request does not need.

### Website asset

```
Use case: <photorealistic-natural|stylized-concept|product-mockup|infographic-diagram|ui-mockup>
Asset type: <hero image / section illustration / blog header>
Primary request: <short description>
Scene/backdrop: <environment or abstract backdrop>
Subject: <main subject>
Style/medium: <photo/illustration/3D>
Composition/framing: <wide/centered; note usable negative space only if needed>
Lighting/mood: <soft/bright/neutral>
Color palette: <brand colors or neutral>
Constraints: <no text; no logos; no watermark; leave room for UI if needed>
```

Worked — landing page hero background:

```
Use case: stylized-concept
Asset type: landing page hero background
Primary request: minimal abstract background with a soft gradient and subtle texture
Style/medium: matte illustration / soft-rendered abstract background
Composition/framing: wide composition with usable negative space for page copy
Lighting/mood: gentle studio glow
Color palette: restrained neutral palette
Constraints: no text; no logos; no watermark
```

Worked — blog header image:

```
Use case: photorealistic-natural
Asset type: blog header image
Primary request: overhead desk scene with notebook, pen, and coffee cup
Scene/backdrop: warm wooden tabletop
Style/medium: photorealistic photo
Composition/framing: wide crop with clean room for page copy
Lighting/mood: soft morning light
Constraints: no text; no logos; no watermark
```

### Game asset

```
Use case: stylized-concept
Asset type: <game environment concept art / game character concept / game UI icon / tileable game texture>
Primary request: <biome/scene/character/icon/material>
Scene/backdrop: <location + set dressing> (if applicable)
Subject: <main focal element(s)>
Style/medium: <realistic/stylized>; <concept art / character render / UI icon / texture>
Composition/framing: <wide/establishing/top-down>; <camera angle>; <focal point placement>
Lighting/mood: <time of day>; <mood>; <volumetric/fog/etc>
Constraints: no logos or trademarks; no watermark
```

Worked — UI icon, and a tileable texture:

```
Use case: stylized-concept
Asset type: game UI icon
Primary request: round shield icon with a subtle rune pattern
Style/medium: painted game UI icon
Composition/framing: centered icon; generous padding; clear silhouette
Constraints: no text; no background scene elements; no logos or trademarks; no watermark
```

```
Use case: stylized-concept
Asset type: tileable game texture
Primary request: worn sandstone blocks
Style/medium: seamless tileable texture; PBR-ish look
Scene/backdrop: neutral lighting reference only
Constraints: seamless edges; no obvious focal elements; no text; no logos or trademarks; no watermark
```

### Wireframe

```
Use case: ui-mockup
Asset type: website wireframe
Primary request: <page or flow to sketch>
Style/medium: low-fi grayscale wireframe
Composition/framing: <landscape or portrait to match expected device>
Subject: <sections in order; grid/columns; key labels>
Constraints: no color; no logos; no real photos; no watermark
```

Worked — SaaS homepage:

```
Use case: ui-mockup
Asset type: website wireframe
Primary request: SaaS homepage layout with clear hierarchy
Style/medium: low-fi grayscale wireframe
Subject: top nav; hero with headline and CTA; three feature cards; testimonial strip; pricing preview; footer
Composition/framing: landscape desktop layout
Constraints: label major blocks; no color; no logos; no real photos; no watermark
```

### Logo

```
Use case: logo-brand
Asset type: logo concept
Primary request: <brand idea or symbol concept>
Style/medium: vector logo mark; flat colors; minimal
Composition/framing: centered mark; clear silhouette; generous margin
Color palette: <1-2 colors; high contrast>
Text (verbatim): "<exact name>" (only if needed)
Constraints: no gradients; no mockups; no 3D; no watermark
```

Worked — wordmark:

```
Use case: logo-brand
Asset type: logo concept
Primary request: clean wordmark for a modern studio
Style/medium: vector wordmark; flat colors; minimal
Text (verbatim): "Studio North"
Composition/framing: centered text; even letter spacing
Constraints: no gradients; no mockups; no 3D; no watermark
```

## Recipes — edit

### text-localization

```
Use case: text-localization
Input images: Image 1: original infographic
Primary request: replace "Bean Hopper", "Grinder", "Brew Group", "Boiler", "Water Tank", and "Drip Tray" with "Tolva", "Molino", "Grupo de infusión", "Caldera", "Depósito de agua", and "Bandeja de goteo"
Constraints: change only the text; preserve layout, typography, spacing, and hierarchy; no extra words; do not alter logos or imagery
```

### identity-preserve

```
Use case: identity-preserve
Input images: Image 1: person photo; Image 2..N: clothing references
Primary request: replace only the clothing with the provided garments
Constraints: preserve face, body shape, pose, hair, expression, and identity; match lighting and shadows; keep the background unchanged; no accessories or text
```

### precise-object-edit

```
Use case: precise-object-edit
Input images: Image 1: room photo
Primary request: replace only the white chairs with wooden chairs
Constraints: preserve camera angle, room lighting, floor shadows, and surrounding objects; keep all other aspects unchanged
```

### lighting-weather

```
Use case: lighting-weather
Input images: Image 1: original photo
Primary request: make it look like a winter evening with gentle snowfall
Constraints: preserve subject identity, geometry, camera angle, and composition; change only lighting, atmosphere, and weather
```

### background-extraction

```
Use case: background-extraction
Input images: Image 1: product photo
Primary request: isolate the product on a clean transparent background
Constraints: crisp silhouette; no halos or fringing; preserve label text exactly; no restyling
```

### style-transfer

```
Use case: style-transfer
Input images: Image 1: style reference
Primary request: apply Image 1's visual style to a man riding a motorcycle on a plain white backdrop
Constraints: preserve palette, texture, and brushwork; no extra elements
```

### compositing

```
Use case: compositing
Input images: Image 1: base scene; Image 2: subject to insert
Primary request: place the subject from Image 2 next to the person in Image 1
Constraints: match lighting, perspective, and scale; keep the base framing unchanged; no extra elements
```

### sketch-to-render

```
Use case: sketch-to-render
Input images: Image 1: drawing
Primary request: turn the drawing into a photorealistic image
Constraints: preserve layout, proportions, and perspective; choose realistic materials and lighting; do not add new elements or text
```
