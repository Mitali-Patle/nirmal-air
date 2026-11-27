---
name: NirmalAir
description: Today's measured air as one quiet day rail on paper, for each person at home.
colors:
  morning-sky: "#F2F1EC"
  morning-bar-sky: "#FAFAF6"
  morning-smog: "#B5AC9B"
  morning-ink: "#1C1E1C"
  morning-muted: "#55544D"
  morning-panel: "#FBFBF8"
  morning-line: "#DAD8CF"
  morning-sky-high: "#B4D2E8"
  afternoon-sky: "#F3F0E8"
  afternoon-bar-sky: "#FAF8F2"
  afternoon-smog: "#B6AB97"
  afternoon-ink: "#1D1E1B"
  afternoon-muted: "#57534A"
  afternoon-panel: "#FBFAF6"
  afternoon-line: "#DDD7CB"
  afternoon-sky-high: "#C4D6E0"
  evening-sky: "#F1E8DA"
  evening-bar-sky: "#F8F2E8"
  evening-smog: "#B3A58F"
  evening-ink: "#1F1C17"
  evening-muted: "#574F43"
  evening-panel: "#FBF7F0"
  evening-line: "#DCCFBB"
  evening-sky-high: "#E8AE7E"
  dusk-sky: "#1A1832"
  dusk-bar-sky: "#15132B"
  dusk-smog: "#36323F"
  dusk-ink: "#EEEAF2"
  dusk-muted: "#B6B0CC"
  dusk-panel: "#221F3D"
  dusk-line: "#363256"
  dusk-sky-high: "#3E3670"
  night-sky: "#0E1730"
  night-bar-sky: "#0B1328"
  night-smog: "#2C3140"
  night-ink: "#EDEFF5"
  night-muted: "#A9B2C8"
  night-panel: "#15213C"
  night-line: "#263354"
  night-sky-high: "#1F3263"
  brand-sky: "#173A2A"
  brand-bar-sky: "#133224"
  brand-ink: "#F2EFE6"
  brand-muted: "#BFD0C3"
  brand-panel: "#1E4633"
  brand-line: "#2E5A44"
  brand-accent: "#E9C46A"
  brand-on-accent: "#1B1A12"
  accent: "#2D5A3A"
  accent-evening: "#2B5637"
  accent-dark: "#8DC59B"
  on-accent: "#FFFFFF"
  on-accent-dark: "#10201A"
  home: "#34506F"
  home-evening: "#344E6C"
  home-dusk: "#AFC3E8"
  home-night: "#AFC6EC"
  warn: "#8A5A00"
  warn-evening: "#864F00"
  warn-dark: "#E3B35C"
  band-good: "#00A650"
  band-satisfactory: "#8FC93A"
  band-moderate: "#F5D90A"
  band-poor: "#F28C1C"
  band-very-poor: "#E02424"
  band-severe: "#8E1616"
  kind-measured: "#3E9A5A"
  kind-forecast: "#5B7FA8"
  kind-estimate: "#C08A2E"
  kind-guidance: "#8A8478"
  kind-household: "#8C6FAE"
typography:
  display:
    fontFamily: "Anek Latin, Anek Devanagari, Noto Sans, system-ui, sans-serif"
    fontSize: "clamp(2.125rem, 6vw, 3.25rem)"
    fontWeight: 650
    lineHeight: 1.06
    letterSpacing: "-0.025em"
    fontVariation: "'wdth' 86"
  headline:
    fontFamily: "Anek Latin, Anek Devanagari, Noto Sans, system-ui, sans-serif"
    fontSize: "clamp(2rem, 1.2rem + 2.6vw, 3.25rem)"
    fontWeight: 650
    lineHeight: 1.08
    letterSpacing: "-0.02em"
    fontVariation: "'wdth' 86"
  wordmark:
    fontFamily: "Anek Latin, Anek Devanagari, Noto Sans, system-ui, sans-serif"
    fontSize: "clamp(1.75rem, 1.2rem + 1.4vw, 2.5rem)"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "-0.015em"
    fontVariation: "'wdth' 86"
  title-next:
    fontFamily: "Anek Latin, Anek Devanagari, Noto Sans, system-ui, sans-serif"
    fontSize: "clamp(1.5rem, 4.6vw, 2rem)"
    fontWeight: 650
    lineHeight: 1.12
    letterSpacing: "-0.015em"
    fontVariation: "'wdth' 86"
  title:
    fontFamily: "Anek Latin, Anek Devanagari, Noto Sans, system-ui, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: "-0.01em"
    fontVariation: "'wdth' 86"
  body:
    fontFamily: "Anek Latin, Anek Devanagari, Noto Sans, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.55
    fontFeature: "tnum"
  step:
    fontFamily: "Anek Latin, Anek Devanagari, Noto Sans, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 600
    lineHeight: 1.3
  label:
    fontFamily: "Anek Latin, Anek Devanagari, Noto Sans, system-ui, sans-serif"
    fontSize: "0.6875rem"
    fontWeight: 500
    lineHeight: 1
    letterSpacing: "0.01em"
  figure:
    fontFamily: "Anek Latin, Anek Devanagari, Noto Sans, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 600
    lineHeight: 1.4
    fontFeature: "tnum"
rounded:
  hour: "2px"
  swatch: "3px"
  pin: "4px"
  control: "10px"
  panel: "14px"
  pill: "999px"
spacing:
  "1": "4px"
  "2": "8px"
  "3": "12px"
  "4": "16px"
  "5": "24px"
  "6": "32px"
  "7": "48px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    rounded: "{rounded.control}"
    padding: "10px 18px"
    height: "44px"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.afternoon-ink}"
    rounded: "{rounded.control}"
    padding: "10px 18px"
    height: "44px"
  button-pressed:
    backgroundColor: "{colors.afternoon-ink}"
    textColor: "{colors.afternoon-sky}"
    rounded: "{rounded.control}"
  input-text:
    backgroundColor: "{colors.afternoon-panel}"
    textColor: "{colors.afternoon-ink}"
    rounded: "{rounded.control}"
    padding: "10px 12px"
    height: "44px"
  panel-side:
    backgroundColor: "{colors.afternoon-panel}"
    rounded: "{rounded.panel}"
    padding: "16px 24px 24px"
  kind-label:
    backgroundColor: "{colors.afternoon-panel}"
    textColor: "{colors.afternoon-muted}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "4px 8px 4px 7px"
  live-pill:
    textColor: "{colors.afternoon-muted}"
    rounded: "{rounded.pill}"
    padding: "7px 12px 7px 10px"
  band-swatch:
    rounded: "{rounded.swatch}"
    size: "11px"
  now-pin:
    backgroundColor: "{colors.afternoon-ink}"
    textColor: "{colors.afternoon-panel}"
    rounded: "{rounded.pin}"
    padding: "0 6px"
---

# Design System: NirmalAir

## Overview

**Creative North Star: "The Day on Paper"**

The household's day is one quiet timeline. Each person's step is a dot on a hairline rail; the next step is set large in condensed Anek; every other step is a calm row with its figure at the right edge. The page follows the local sky: `<html data-phase>` comes from the place's sunrise and sunset (morning, afternoon, evening are warm paper with near-black ink; dusk is deep indigo, night midnight blue, both with pale ink), and `data-haze` (0 to 5) from the measured AQI band dulls the ground toward smog. After dusk a faint fixed star field sits behind the whole Today page and thins with the haze. A user can pin light or dark; "Follow the sky" follows only the sky, whatever the device's dark-mode setting, so the page never shows a daytime sun on a night ground.

It refuses the AQI dashboard (gauge, giant number, pollutant tiles), the bright card-stack wellness app, and the road-sign boards an earlier version used. The air's severity is said in words, never shouted in colour.

**Key Characteristics:**
- Paper and ink by day, indigo and midnight by night: five phases, six haze levels, all AA-tested.
- One deep green for actions and people; a slate blue only for the home.
- One family, Anek (Ek Type), for every word and number, in Latin and Devanagari.
- Hairlines and tone instead of shadows; 10px and 14px corners.
- A softened sky band under the top bar on Today, drawn from the real sun, cloud and rain.

## Colors

Five phase palettes, one green, one slate blue, and CPCB colour kept to a swatch.

### Brand (start and error pages)
Pages without a household's sky wear the brand: **Forest** ground (`brand-sky`) and bar, pale ink, and **Marigold** (`brand-accent`) for actions, in every light or dark setting (`html[data-phase="brand"]`). Opening a household hands the page to the place's sky, so the change of colour marks the step from the product to the family's own day. `tests/test_contrast.py` checks it like the five sky phases.

### Primary
- **Ledger Green** (`accent`; `accent-evening` at evening, `accent-dark` at dusk and night): every action (buttons, the link button, selection, focus ring, caret, form accent) and every person's step (rail dot, the name under the step). Its 14% mix into the panel (`--accent-tint`) rings the next-step dot and backs the sample-household tag. Text on it is `on-accent` (`on-accent-dark` after dusk).

### Secondary
- **Slate Home Blue** (`home` and its phase variants): only steps about the home, on the dot and the step's "who" line.

### Tertiary
- **Calm Amber** (`warn` and variants): the standard-advice label and form errors, always as a 14% tint (`--warn-tint`) with an amber-edged border, and the hatched worst hour on the 24-hour strip. Text on it stays ink.

### Neutral
- **Phase Ground** (`<phase>-sky`): the page ground. Rendered as `--ground`, smog mixed in at the haze share (0, 4, 7, 10, 14, 18%). Warm paper in the light phases, Deep Indigo at dusk, Midnight Blue at night.
- **Bar Ground** (`<phase>-bar-sky`): the top bar, hazed the same way (`--bar`).
- **Panel** (`<phase>-panel`): side panels, form groups, fact labels, the numbers behind a step.
- **Ink / Muted Ink** (`<phase>-ink`, `<phase>-muted`): text and secondary text.
- **Hairline** (`<phase>-line`): every divider, border and the rail itself.
- **Smog** (`<phase>-smog`): never painted directly; only mixed into the ground and laid over the sky band as its haze veil.
- **High Sky** (`<phase>-sky-high`, in `sky.css`): the top of the sky band, mixed 85% into the ground.

### Band and kind colours
- **CPCB bands** (`band-*`): the official AQI band colours, used only as the band swatch.
- **Fact kinds** (`kind-*`): a 6px dot inside each fact label (measured, forecast, estimate, guidance, household); the word is the label. `kind-measured` is also the live dot in the top bar.

### Named Rules
**The Swatch-Only Rule.** A CPCB band colour appears only as an 11px swatch beside the band's name. Never as a fill, a text colour, a border or a background.

**The One Green Rule.** Green carries every action and every person's step; blue marks only the home. No third accent.

**The Every-Phase Contrast Rule.** `tests/test_contrast.py` checks ink, muted, accent and home against sky and bar-sky at all six haze levels in all five phases, and against panel; on-accent on accent in every phase; and that the dark-mode block equals the night palette. Any new text colour or ground goes into that test before it ships.

## Typography

**Display Font:** Anek Latin variable (weight 100 to 800, width 75 to 125%), headings at 86% width
**Body Font:** Anek Latin, with Anek Devanagari (400 to 700) for Hindi, then Noto Sans, system-ui
**Label/Mono Font:** none; figures are Anek 600 in tabular numerals

**Character:** One humanist sans from the Indian foundry Ek Type, chosen after research for small-screen legibility and because its Latin and Devanagari match, so the Hindi plan is set as carefully as the English one. Headings narrow to 86% width (`--display-stretch`) at 650 to 700, the way Indian newspapers set their heads; text stays open at 400. Self-hosted woff2 in `public/static/fonts` (latin, latin-ext, devanagari subsets by unicode-range); the latin file is preloaded. Numerals are tabular on the whole page.

### Hierarchy
- **Display** (`display`): the start page headline, 16ch max.
- **Headline** (`headline`): the place name on Today, the largest text on the page.
- **Wordmark** (`wordmark`): "Nirmal" in ink, "Air" in green, in the top bar.
- **Title, next step** (`title-next`): the next step on the rail, the one large step of the day.
- **Title** (`title`): section headings, 1.25rem in the side column and for form-group legends. Weekly totals use the same face at 1.75rem; Ask answers at 1.3125rem weight 600.
- **Step** (`step`): every other step's action. Why-lines 0.9375rem muted, 62ch max.
- **Body** (`body`): 17px/1.55; intro copy 1.0625rem, 54ch max; `.meta` and form labels 0.875rem.
- **Label** (`label`): fact labels. Group heads ("Next", "Later today") and the live pill are 0.8125rem 500 muted.
- **Figure** (`figure`): step figures right-aligned (1.0625rem on the next step); fact figures at 1rem; hour ticks 0.6875rem 400.

### Named Rules
**The One Family Rule.** Every word and number is Anek. Headings change width and weight, never family. No serif, no monospace, no second sans.

**The Narrow Head Rule.** A heading is Anek at 86% width and 650 to 700 weight; text is normal width at 400 to 600. Width is what separates a head from text.

## Layout

A centred page up to 2200px (`--page-max`) whose side gutter grows with the screen (`--gutter`: `clamp(24px, 3.2vw, 64px)`), a 4/8/12/16/24/32/48px spacing scale, and hairline-separated rows rather than cards.

- **Today, phone:** one column: place and air line, the plan rail, the side panels, home, trips, the week.
- **Today, from 960px:** a 7:5 grid, column gap `clamp(48px, 4vw, 96px)`. The plan, home, trips and week stay in the left 7 columns; the right 5 (24-hour strip, what the air means, Ask, how the plan was made) are sticky and scroll on their own.
- **Start, from 1100px:** a 5:7 grid with a 72px gap; the intro and how-it-works rail stay sticky on the left, samples and the household form on the right.
- **Sky band:** 64px on phones, `clamp(96px, 6.8vw, 132px)` from 960px; a narrower drawing below 720px so the sun near sunrise or sunset is not cropped.
- Measures: 46 to 72ch for running text; rows let the figure sit at the right edge.

## Elevation & Depth

Flat. Depth is tone and hairline: panel on ground with a 1px line. The only box-shadows are flat rings, never offsets: the live dot's 3px halo and the next-step dot's 5px tint ring. At dusk and night the star field is a fixed layer behind everything (`z-index: -1`); content and panels sit over it.

### Named Rules
**The Paper-on-Paper Rule.** No drop shadows, glass or blur. A surface lifts by being panel with a hairline edge.

## Shapes

Gently rounded: 10px on controls, inputs, notes and the numbers behind a step; 14px on side panels and form groups; full pills for fact labels, the live status and the sample tag. Small marks stay small: 3px swatch corners, 2px hour cells, 4px on the now-pin and focus ring. Circles are the rail's language: 13px outlined dots, the 15px filled next dot, 21px numbered rings on the start page. Chevrons are drawn (an SVG stroke, or a rotated 1.5px border corner on disclosures), never glyphs.

## Components

### Buttons
- **Shape:** gently rounded (10px), 44px minimum height.
- **Primary:** Ledger Green with on-accent text, 600 weight, 10px 18px; the start page's link button is the same at 12px 20px. One primary per view.
- **Hover / Focus:** hover mixes 14% ink into the green; active nudges down 1px; focus is a 2px green outline at 3px offset. Transitions 160ms on the house ease (`cubic-bezier(0.16, 1, 0.3, 1)`).
- **Quiet:** transparent with a hairline border; hover shows panel and a muted border. Pressed (`aria-pressed="true"`) inverts to ink on ground, used for "I did this" and the colour choice.

### Chips (fact labels)
- **Style:** panel pill with a hairline border, muted 11px label, and a 6px kind dot before the word. Sits beside headings and before each fact.

### Cards / Containers
- **Side panels:** panel, 14px corners, hairline border, 16px 24px 24px padding. How-the-plan-was-made is a quiet disclosure row, not a card.
- **Form groups:** the same panel and corner, with a narrow-head legend at 1.25rem.
- **Notes:** panel, 10px corners, 8px 12px.

### Inputs / Fields
- **Style:** panel, hairline border, 10px corners, 10px 12px, 44px high; the Ask input sits on the ground inside its panel.
- **Hover:** border darkens to muted. **Focus:** the global green outline. **Error:** the amber-tint error block above the form.

### Navigation
- **Top bar:** bar ground with a hairline under it. The wordmark, and a live pill (hairline border, measured-green dot): "AQI n" in ink and the measured time on Today, "Live CPCB data" on start.
- **Tools (Today):** under the place name: "Change place or household" and the Hindi link.
- **Colour control (Today, top bar beside the AQI pill):** on phones one 34px round button showing the current mode (moon, half disc, sun); each tap moves dark → follow the sky → light. From 720px a three-way switch of the same drawn icons (32×28px, pill track, the chosen one filled with ink). It repaints in place: htmx swaps the sky band, its note and the control, and an HX-Trigger event sets phase, haze and theme on `<html>` while colours cross-fade for 500ms (none under reduced motion). The request carries the page's haze level, so only the cached weather is read. Below 380px the pill drops the time.
- **Press:** every button and button-link scales to 0.96 while pressed (a sample row to 0.99), then springs back.
- **Footer:** hairline above, muted 13px source line with its links.

### Day Rail (signature)
Each step is a three-column row: a 20px rail column, the text, and a right-edge figure. The 1px hairline runs between dot centres with no loose ends. Person dots are outlined green, home dots outlined blue, on the ground. The next step fills its dot, adds the tint ring and sets the action in `title-next`, its why-line in ink. "The numbers behind this" opens a panel list of labelled facts. While the plan is written, the rail's shape breathes (opacity to 0.45 over 1.4s).

### Air Line
The place's AQI at 1.125rem 600 beside the band name and its swatch, then the muted station line. It is never larger than the place name.

### 24-Hour Strip
24 cells, 16px high, 2px apart and 2px rounded: neutral ink at 12%, cleaner hours green at 32%, dirtier amber at 32%, the cleanest hour solid green, the worst hour an amber hatch. An ink "Now" pin sits over the first hour; ticks below; a legend names the cleanest and worst hours in words.

### Sky Band and Night Sky
Under the top bar on Today only, aria-hidden and carrying no text. Its top stop mixes the phase's high sky 85% into the ground; its lower 55% fades into the ground so it has no edge. Sun or moon sit on the real path for the place; stars, clouds and rain come from real data, positioned by `app/domain/scene.py`. Smog lays a veil over it (opacity 0.06 to 0.25 by haze). Motion plays once on arrival (sun or moon rises over 1.6s, clouds drift in over 1.8s), then only clouds float, stars twinkle and rain falls. At dusk and night `sky.css` also lays six tiled radial-gradient stars, fixed, over the whole Today page behind the content: opacity `0.85 − 2 × veil` at night, `0.45 − veil` at dusk.

## Do's and Don'ts

### Do:
- **Do** set every colour on `<html data-phase data-haze>` and add any new text colour or ground to `tests/test_contrast.py` (The Every-Phase Contrast Rule).
- **Do** say the band in words with its 11px swatch beside it (The Swatch-Only Rule).
- **Do** set headings in Anek at `--display-stretch` (86%) and 650 to 700; figures in Anek 600 with tabular numerals.
- **Do** give each step a named person, a why-line and, when there is one, a figure at the right edge.
- **Do** label every fact with its kind (measured, forecast, estimate, guidance, household).
- **Do** stop all transitions and animations under `prefers-reduced-motion: reduce`, including the sky.
- **Do** keep sun, moon, stars, clouds and rain driven by `app/domain/scene.py`, never placed by hand.

### Don't:
- **Don't** add a gauge, a dial or a giant AQI number; the place name stays the largest text on Today.
- **Don't** use alarm styling: no red, no warning icons, no flashing. Amber appears only as a tint, a border or the worst-hour hatch.
- **Don't** fill, tint or colour text with a CPCB band colour.
- **Don't** add drop shadows, glass, blur or decorative gradients; the sky band, the night star field and the worst-hour hatch are the only gradients.
- **Don't** bring back boards or sign plates; steps are rows on the rail and facts are rows between hairlines.
- **Don't** add a second family: no editorial serif, no monospace, no Inter (The One Family Rule).
- **Don't** put text in the sky band.
