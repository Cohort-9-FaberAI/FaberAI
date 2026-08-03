---
version: anydesign-1
name: Faber AI — Brand Identity
source: Faber_AI.pdf (uploaded brand deck, 7 slides)
captured_at: 2026-08-01
description: |
  Faber AI is an engineering-coded manufacturing intelligence brand. It pairs a single
  electric-blue accent with deep navy and cool neutrals to signal precision, confidence,
  and machine-driven analysis. The identity's central device is a wireframe-to-solid
  isometric mark — a CAD blueprint literally resolving into a finished blue form — which
  encodes the product's core promise (turning raw CAD geometry into manufacturing
  certainty) directly into the logo.

colors:
  primary: "#0858F4"
  ink: "#0B136B"
  surface: "#FFFFFF"
  surface-muted: "#D9D9D9"
  text-on-light: "#0B136B"
  text-on-dark: "#FFFFFF"

typography:
  display:
    fontFamily: "Geist, Inter, system-ui, sans-serif"
    fontWeight: 700
    letterSpacing: "-0.01em"
    note: "Bold/Black wordmark weight seen on title cards, set in ink navy or white"
  accent-italic:
    fontFamily: "Geist SemiBold Italic, Inter, system-ui, sans-serif"
    fontWeight: 600
    fontStyle: italic
    note: "Used for taglines, descriptions, and the type-specimen slide — the 'voice' register"
  body:
    fontFamily: "Geist, Inter, system-ui, sans-serif"
    fontWeight: 400
    lineHeight: 1.4

spacing:
  base: 8px
  scale: [8, 16, 24, 32, 48, 64, 96]

rounded:
  logo-corner: "sharp/chamfered (isometric facets, no border-radius)"

components:
  wireframe-to-solid-logomark:
    style: "isometric wireframe (outline) resolving into solid blue geometric form"
    colorway: "primary (#0858F4) solid + ink/black wireframe outline"
  wordmark-lockup-with-embedded-mark:
    layout: "horizontal, mark left of wordmark, or mark inline replacing a letterform"
    colorway: "ink navy wordmark + blue mark, or reversed (white wordmark + blue mark on blue field)"
---

# Design Analysis — Faber AI Brand Identity

> Analysis generated with the `anydesign` skill.
> Date: 2026-08-01
> Analysis emphasis: mood/reference + design system (brand identity deck; no product UI present)

---

## Source

- **Source type**: local image / PDF (7-slide brand presentation)
- **Path**: `Faber_AI.pdf`
- **Capture method**: direct vision
- **Detected limitations**: This is a **brand identity deck**, not a product UI. There are no
  screens, components, buttons, or layouts from the actual Faber AI software — only logo,
  color, typography, and one moodboard/inspiration slide ("WE COLLABORATE & ADAPT," which
  reads as an external style reference, not Faber AI's own content). Sections 3 and 4
  (Components, Layout) are therefore thin by necessity — flagged accordingly rather than
  invented.

---

## TL;DR

Faber AI's identity is built on one device: a wireframe cube-like mark that resolves halfway
into a solid, saturated blue "AI-verified" form — literally dramatizing "raw CAD data becoming
a validated part." The palette is disciplined (one electric blue, one deep navy, one warm
gray, white), and the wordmark pairs a confident bold sans with an italic secondary voice for
description text, giving the brand a "precision engineering firm that happens to run on AI"
feel rather than a generic SaaS look.

---

## 1. Visual identity

### 1.1 Surface description

**Personality**: precise, confident, technical, minimal, engineered.

**Mood**: calm authority — dark, deep-blue cover slide gives it a premium/serious opening,
then flips to clean white for the working brand pages. Reads as B2B industrial-tech, not
consumer-playful.

**Detectable stylistic references**: the isometric wireframe-to-solid mark is in the same
family as CAD/engineering-software marks (Onshape, Fusion 360-adjacent visual language) and
the dark hero + saturated single-blue accent is common to current "AI infrastructure" brand
covers (Vercel/Linear-adjacent cover convention, but with navy instead of black).

**Information density**: minimalist — each slide isolates one idea (logo, color, or type).

**Implicit positioning**: manufacturing engineers, DFM (design-for-manufacturing) reviewers,
and industrial/operations buyers evaluating an AI CAD-analysis tool — not a consumer or
developer audience.

**Confidence**: ✅ high (directly observed across all 7 slides)

### 1.2 Brand voice / Atmosphere

Faber AI's design behaves like it's speaking to people who distrust hype: manufacturing and
engineering buyers who have been burned by tools that oversell and underdeliver on the shop
floor. Every choice reduces perceived risk rather than performing excitement — the palette
stays at three colors plus white, the type system has exactly two registers (a bold
authoritative face for names/headlines, an italic secondary face for explanatory copy), and
even the "hero" slide is a dark, quiet gradient rather than a busy product screenshot. This is
a brand that believes credibility with engineers is earned through restraint, not spectacle.

The one place the brand allows itself real expression is the logomark, and it does so with
intent rather than decoration: the mark literally depicts a dashed-line wireframe blueprint
resolving into a solid blue volume. That's not abstract geometry picked for being "modern" —
it's a diagram of the product's job (take ambiguous CAD input, return manufacturing
certainty), which means the logo is doing brand *and* product-explanation work simultaneously.
Everything else in the system — the navy/blue duotone, the flat color blocking, the absence of
gradients or textures outside the cover slide — exists to keep that one symbol legible and
un-competed-with.

### 1.3 The "ONE brand thing"

- **The thing**: the wireframe-to-solid isometric mark — an outlined, dashed-construction-line
  cube/bracket form on the left that resolves into a filled `{colors.primary}` (#0858F4) solid
  form on the right, sharing a continuous silhouette.
- **Why it carries the brand**: it's the only element in the deck that encodes what the
  product *does* (not just what industry it's in). Remove it and Faber AI becomes a generic
  "blue tech" brand indistinguishable from dozens of B2B SaaS logos.
- **How everything else supports it**: the palette is deliberately reduced to let the mark's
  blue read as singular and intentional; typography stays plain-geometric so it never competes
  visually with the mark's angularity; backgrounds are flat fields (white, light gray, or
  solid blue) so the wireframe/solid contrast inside the mark is never fighting a busy
  background.
- **Where it appears (and where it deliberately doesn't)**: it appears standalone (full
  wireframe-to-solid detail), in the compact lockup with the wordmark, and reversed in white
  on a blue field for the "on-brand-color" variant. It never appears filled-in mid-italic
  text or shrunk into a favicon-scale treatment in this deck — its detail (dashed construction
  lines) implies a minimum legible size, likely why the wordmark-only lockup exists for small
  placements. ⚠️ *inferred minimum-size rule — not explicitly stated in the deck.*

*Confidence*: ✅ high on the mark's construction and centrality; ⚠️ medium on the "where it
doesn't appear" scoping rule, since only 7 slides are available.

---

## 2. Design System (tokens)

### 2.1 Colors

| Token | Hex | Role | Where it appears | Confidence |
|---|---|---|---|---|
| `primary` | `#0858F4` | Brand accent / "AI-verified" solid fill | Logo solid half, cover gradient highlights, swatch slide, blue background variant | ✅ high — labeled explicitly on swatch slide |
| `ink` | `#0B136B` | Deep navy — wordmark color, dark surface | Wordmark text on white slides, dark swatch bar | ✅ high — labeled explicitly on swatch slide |
| `surface` | `#FFFFFF` | Base background | Logo lockup slides, type behind wordmark | ✅ high |
| `surface-muted` | `#D9D9D9` | Neutral gray background | Logo-on-gray demonstration slide, swatch bar | ✅ high — labeled explicitly on swatch slide |

The cover slide uses a dark **navy-to-near-black gradient with a violet undertone** (top-right
trending toward `#0B0B1A`-ish black, blending through indigo/purple into the mid-tone navy) —
this is a decorative gradient, not a flat token; treat it as a one-off hero effect rather than
a reusable swatch. ⚠️ medium confidence on exact gradient stops (estimated from image, not
sampled).

No dark-mode UI token set exists in this material — only the dark **cover slide** and the
**inverted logo-on-blue** treatment were observed.

### 2.2 Typography

- **Detected family**: `Geist` — confirmed explicitly on the type specimen slide, labeled
  "Geist SemiBold Italic." ✅ high confidence (named directly in the source).
- **Suggested fallback**: `Inter, system-ui, sans-serif` (Geist's closest widely-available
  geometric-grotesk relative).

**Observed styles:**

| Token | Style | Weight | Use |
|---|---|---|---|
| `display` (wordmark) | Upright, tight | Bold/Black (~700–800) | "Faber AI" wordmark on all lockup slides |
| `accent-italic` | Italic | SemiBold (600) | Taglines ("The intelligent manufacturing expert"), body description, full type specimen |
| `section-label` | Upright | Bold (~700) | "Color System:" label |

The deck deliberately pairs **upright bold** (identity/naming) with **italic semibold**
(explaining/describing) — a two-register system rather than a full type scale. No light or
regular non-italic body weight is shown in this material.

**Notable detail**: the italic register carries real brand weight here — it's not a
default/fallback style, it's used for the entire type-specimen showcase, meaning Geist SemiBold
Italic is likely the brand's primary "voice" style for supporting copy, not just emphasis.

### 2.3 Spacing

⚠️ Low confidence — this is a slide deck, not a UI, so spacing is compositional (slide margins,
element gaps) rather than a system with reusable tokens. Observed margins are generous and
consistent (content sits inboard of an implied ~64–96px slide gutter on the 1456px-wide
frames), consistent with an 8px-based scale, but this is an inference, not a measured token.

### 2.4 Radii

No rounded UI elements are present. The logomark itself uses sharp, chamfered isometric facets
— zero border-radius anywhere in the material. If Faber AI builds UI from this identity, a
**sharp-to-slightly-softened** radius scale (e.g., 4–8px) would match the engineering/CAD tone
better than a pill/rounded-heavy scale — ⚠️ this is a recommendation, not an observed token.

### 2.5 Elevation system

Not applicable / not observed — no cards, shadows, or layered UI surfaces appear anywhere in
this material. *Say so explicitly rather than fabricate a tier system.*

#### Decorative depth (non-functional)

- **Cover gradient**: a dark, diagonal, wave-like navy/violet/black mesh gradient fills the
  entire first slide behind the wordmark — the only atmospheric effect in the deck, scoped
  exclusively to the cover/title moment.
- **Logo internal shading**: none — the mark uses flat fills and thin outline strokes only,
  no gradient or bevel inside the mark itself, which keeps it reproducible at any size/medium.

### 2.6 Borders

- Logo wireframe strokes: thin (~1–2px equivalent at deck scale), color `ink`/near-black,
  used only for the "blueprint" half of the mark and for construction/dashed guide lines.
- Dashed lines specifically mark **construction geometry** inside the mark (a CAD-drawing
  convention) — this is a deliberate signal, not decoration, and should be preserved as dashed
  (not solid) if the mark is redrawn.

### 2.7 Accessibility quick-check

Two clear text/surface pairs are available from the material:

- `ink` (#0B136B) on `surface` (#FFFFFF): very high contrast — reads comfortably as body/
  headline text. ✅ AA/AAA safe at any size (deep navy on white is a strong pairing well above
  WCAG thresholds).
- `surface` (#FFFFFF) on `primary` (#0858F4): white text/wordmark on the solid blue field
  slide — a mid-toned saturated blue, so this pairing is safe for large/bold text but should
  be verified at small sizes before use in body copy; recommend bold weight ≥18px if reused
  in UI. ⚠️ medium confidence — exact ratio not computed against the sampled hex (visual
  estimate, not run through a contrast script).

---

## 3. Components Inventory

### 3.1 Generic components

No generic UI components (buttons, inputs, cards, nav) appear in this material — the deck is
brand-asset documentation only (logo lockups, color swatches, a type specimen). *State this
explicitly rather than infer UI patterns that weren't shown.*

### 3.2 Signature components

#### Wireframe-to-Solid Logomark
- **What it is**: an isometric geometric form (reads as a stylized "F" or bracket shape)
  split down its diagonal — the left/upper portion rendered as an open outline with dashed
  internal construction lines (CAD blueprint style), the right/lower portion rendered as a
  flat solid fill in `{colors.primary}` (#0858F4).
- **Why it's signature**: it's the only element that visually explains the product category
  (CAD analysis) rather than just the brand tone. No competitor-neutral generic mark would
  encode "blueprint becomes verified part" this literally.
- **Composition**: outline stroke in dark ink/near-black, dashed guide lines in a lighter
  blue-gray, solid fill in `{colors.primary}`. Built on an isometric (30°) grid, consistent
  across every logo slide.
- **Where it appears**: full-detail version (with dashed construction lines) on the
  "wordmark replacement" and "color variants" slides; a simplified/reduced-line version
  (construction lines mostly dropped) as the compact companion mark next to the wordmark on
  the intro slide — suggesting a **full mark for hero/brand moments** and a **simplified mark
  for lockups**, though this reduction isn't formally documented as a rule in the deck.
- **Confidence**: ✅ high on the form and coloring; ⚠️ medium on the full-vs-simplified usage
  rule (inferred from comparing slides, not stated).

#### Wordmark Lockup with Embedded Mark
- **What it is**: on one slide, the logomark is inset directly into the wordmark, replacing
  the counter of the "a" in "Faber" — mark and type sharing a single silhouette.
- **Why it's signature**: shows the identity system was designed with the mark and wordmark
  as a single integrated unit, not just a logo-plus-text pairing bolted together.
- **Composition**: wordmark in `ink`, mark inset at the "a" position, scaled to match cap-height.
- **Where it appears**: one dedicated exploration slide only — likely a lockup *option* shown
  alongside the standard side-by-side lockup, not necessarily the primary approved usage.
- **Confidence**: ⚠️ medium — shown once, unclear if this is the primary or an alternate lockup.

---

## 4. Layout & Composition

### 4.1 Grid & containers

Standard 16:9 slide frames (1456×816-equivalent). Content is generally split into clear halves
(left: text/wordmark, right: visual/mark) or full-bleed color blocks — a simple two-zone
compositional habit repeated across the logo and color slides.

### 4.2 Composition patterns

- **Cover pattern**: full-bleed dark gradient, centered-left large wordmark.
- **Split pattern**: left text column (wordmark + headline + italic description) / right
  visual (logomark), used on the intro slide.
- **Comparison pattern**: side-by-side panels on neutral gray to show the mark isolated vs.
  the mark with wordmark (construction/detail view vs. final lockup).
- **Swatch pattern**: full-bleed vertical color bars, hex code labeled bottom-left in italic
  caption type.
- **Moodboard tile pattern**: on the final slide, a rotated grid of poster tiles ("WE
  COLLABORATE & ADAPT") — this reads as an **external inspiration/reference board**, not
  Faber AI's own applied brand system, since the palette (black/white/blue with architectural
  photography) and typographic treatment (all-caps condensed sans) don't match the Faber AI
  tokens defined elsewhere in the deck. ⚠️ flagged as reference material, not brand system,
  see Open Questions.

### 4.3 Responsive behavior

Not applicable — this is a static brand/print-style deck, not a responsive digital surface. No
breakpoint or viewport information is present.

### 4.4 Image behavior

- **Logomark**: vector-style flat geometric artwork, reproduced at consistent scale relative
  to the wordmark; always on a solid (never photographic) background in this deck.
- **Cover gradient**: full-bleed decorative mesh/wave gradient, no crop artifacts, purely
  atmospheric.
- **Moodboard tile photography**: architectural line-drawing and photographic textures appear
  only on the final reference slide, cropped into rotated poster tiles — isolated to that one
  slide and not reused elsewhere.

---

## 5. Reconstruction Notes

### Suggested stack

**Design tokens + SVG/vector logo asset, not a component framework.** This material documents
a *brand*, not a *UI*. If Faber AI's product interface needs to be built, treat this design.md
as the token/voice source of truth and pair it with a standard system (Tailwind + shadcn/ui
would suit the restrained, engineering tone well) rather than trying to "reconstruct" screens
that were never shown.

### Quick wins

- Palette and the Geist/Geist-italic type pairing are fully specified and trivial to apply
  (`{colors.primary}`, `{colors.ink}`, `{colors.surface-muted}` cover 100% of the observed
  system).
- The logomark is clean enough to redraw as SVG directly from the deck at any scale.

### Tricky bits

- The logomark's dashed construction-line detail will disappear at small sizes (favicon,
  nav bar) — a simplified/solid-only version needs to be produced and formalized (a start
  exists on the intro-slide lockup, but it isn't a finished, documented "minimum size" asset).
- Geist SemiBold Italic as a primary body/description voice is unusual — confirm whether this
  extends to long-form product copy or is reserved for marketing headlines/taglines only,
  since italic body text at length hurts readability.
- The cover gradient's exact color stops weren't sampled — needs a designer to re-export or
  re-sample from source files if pixel-exact reproduction is required.

### Implicit states to define

Not observed anywhere in this material — this deck contains zero interactive UI, so hover,
focus, loading, empty, and error states all need to be designed from scratch using
`{colors.primary}` as the interactive/focus color and `{colors.ink}` as the base text color as
starting points.

### Confidence map

| Layer | Confidence | Why |
|---|---|---|
| Identity | ✅ high | Full logo system, cover, and 7 dedicated slides |
| Colors | ✅ high | Hex values explicitly labeled on the swatch slide |
| Typography | ✅ high (family) / ⚠️ medium (full scale) | Family named directly; only one weight/style pair shown, no full type scale |
| Spacing | ❓ low | No UI grid present; only slide-composition margins to infer from |
| Components | ❓ low | No generic UI components in the source material at all |
| Layout | ⚠️ medium | Only static slide compositions, no responsive/product layout |

---

## 6. Do's and Don'ts

### Do

- **Reserve `{colors.primary}` (#0858F4) for the "solid/resolved" half of the brand story.**
  Use it as the singular accent — CTAs, the mark's solid fill, key data highlights — never as
  a decorative background wash.
- **Keep dashed construction lines dashed, not solid, whenever the wireframe half of the
  logomark is redrawn.** The dash is a CAD-blueprint signal core to the "raw geometry" meaning.
- **Pair upright bold type for naming/identity with Geist SemiBold Italic for explanatory
  copy.** This two-register system (not a full weight ramp) is the brand's typographic voice.
- **Keep backgrounds flat** (`{colors.surface}` white, `{colors.surface-muted}` gray, or solid
  `{colors.primary}` blue) behind the logomark. Never place it over photography or gradients
  outside the cover slide.
- **Use the dark cover gradient only once per experience** (as an opening/hero moment) — it's
  a decorative one-off, not a reusable background pattern.
- **Use `{colors.ink}` (#0B136B), not pure black, as the dark neutral** for wordmark and body
  text — it's warmer/bluer than black and part of the deliberate three-color-plus-white system.

### Don't

- **Don't introduce a second accent color.** The system runs on exactly one saturated hue
  (`primary`) plus one dark neutral (`ink`) plus one light neutral (`surface-muted`) — adding
  a second bright color flattens the "one resolved answer" meaning the blue carries.
- **Don't round the logomark's facets or soften its isometric angles.** Sharp, chamfered
  geometry is core to the "engineering precision" read; rounding it drifts toward generic
  consumer-tech.
- **Don't set long-form body copy in the italic register at small sizes without testing
  readability** — it's confirmed as the brand voice for short copy/taglines, not verified for
  paragraphs of product documentation.
- **Don't shrink the full-detail (dashed-line) logomark below a size where the construction
  lines stay legible.** Use the simplified/solid lockup version instead at small scale.
- **Don't reuse the final slide's black/white/architectural moodboard aesthetic as if it were
  Faber AI's own visual system** — it appears to be external inspiration material, not an
  approved brand application (see Open Questions).

---

## 7. Open Questions

- Is the final slide ("WE COLLABORATE & ADAPT" poster grid) an **inspiration/mood reference**
  the Faber AI team is drawing from, or is it meant to be **applied Faber AI marketing
  material**? The typography, all-caps condensed treatment, and monochrome-plus-blue
  photographic style don't match the Geist/Geist-italic + flat-color system defined on the
  other six slides — flagging this as likely reference material, but the source deck doesn't
  label it either way.
- What is the **full type scale** (headline/h1/h2/body/caption sizes and weights)? Only one
  upright-bold style and one italic-semibold style are shown — no size ramp or a regular
  (non-italic, non-bold) body weight is demonstrated.
- Is there a **secondary/non-italic body font** for long-form UI or documentation text, or is
  Geist (upright, regular weight) intended to fill that role by extension?
- What are the **exact gradient stops** on the cover slide? Only visually estimated here —
  needs source Figma/Illustrator file or a color-extraction pass on the original asset for
  pixel-exact hex values.
- Does Faber AI have a **dark-mode product UI** planned, or is dark treatment reserved for
  marketing/brand moments only (as seen here)?
- Is there an **approved minimum size / clear-space rule** for the logomark? A full-detail and
  a simplified version both appear, but no explicit usage rule accompanies them.

---

## 8. Companion files

- [x] `design-tokens.json` — structured tokens in W3C DTCG format
- [ ] `design-a11y.md` — not generated; only one strong pair (`ink`/`surface`) and one
      medium-confidence pair (`surface`/`primary`) were available, and the source has no
      product UI to validate against — can generate on request once more material exists
- [ ] `design-screenshot.png` — not applicable; original PDF pages serve as the visual record

---

*End of analysis. Since this deck documents brand identity rather than a product UI, the next
useful step is likely either (a) converting this into a prompt for Claude Code / v0 to scaffold
an actual Faber AI product UI using these tokens, or (b) formalizing the open logo-usage
questions (minimum size, simplified-mark rule, moodboard-slide status) with whoever produced
the original deck. Let me know which direction is useful, or bring more material (product
screens, the source design file) to sharpen the Components and Layout sections.*
