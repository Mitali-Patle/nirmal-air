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
  dusk-sky: "#1C1A20"
  dusk-bar-sky: "#222027"
  dusk-smog: "#3A3631"
  dusk-ink: "#EEEAF0"
  dusk-muted: "#B4AEBA"
  dusk-panel: "#25232A"
  dusk-line: "#3A3741"
  dusk-sky-high: "#3B3052"
  night-sky: "#161513"
  night-bar-sky: "#1C1B18"
  night-smog: "#34302A"
  night-ink: "#EDE9E0"
  night-muted: "#ABA597"
  night-panel: "#1E1D1A"
  night-line: "#34322D"
  night-sky-high: "#0D0F15"
  accent: "#2D5A3A"
  accent-evening: "#2B5637"
  accent-dark: "#8DC59B"
  on-accent: "#FFFFFF"
  on-accent-dark: "#10201A"
  home: "#34506F"
  home-evening: "#344E6C"
  home-dusk: "#A3BADB"
  home-night: "#9DB6D6"
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
    fontFamily: "Newsreader, Noto Serif Devanagari, Georgia, serif"
    fontSize: "clamp(2.125rem, 6vw, 3.25rem)"
    fontWeight: 500
    lineHeight: 1.06
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Newsreader, Noto Serif Devanagari, Georgia, serif"
    fontSize: "clamp(1.75rem, 5vw, 2.5rem)"
    fontWeight: 500
    lineHeight: 1.08
    letterSpacing: "-0.02em"
  title-next:
    fontFamily: "Newsreader, Noto Serif Devanagari, Georgia, serif"
    fontSize: "clamp(1.5rem, 4.6vw, 2rem)"
    fontWeight: 500
    lineHeight: 1.12
    letterSpacing: "-0.015em"
  title:
    fontFamily: "Newsreader, Noto Serif Devanagari, Georgia, serif"
    fontSize: "1.375rem"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "-0.015em"
  body:
    fontFamily: "Hanken Grotesk, Noto Sans, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
    fontFeature: "tnum"
  step:
    fontFamily: "Hanken Grotesk, Noto Sans, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 600
    lineHeight: 1.3
  label:
    fontFamily: "Hanken Grotesk, Noto Sans, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "0.6875rem"
    fontWeight: 500
    lineHeight: 1
    letterSpacing: "0.01em"
  figure:
    fontFamily: "JetBrains Mono, ui-monospace, Cascadia Mono, monospace"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.4
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

The household's day is one quiet timeline on paper. Each person's step is a dot on a hairline rail; the next step is set large in a book serif; every other step is a calm row with its figure at the right edge. Light phases are warm paper with near-black ink, dusk and night are warm near-black with paper-coloured ink, and the page follows the local sky: `<html data-phase>` comes from the place's sunrise and sunset, and `data-haze` (0 to 5) from the measured AQI band dulls the paper toward smog. A user can pin light or dark; "Follow the sky" in dark mode uses the night palette.

It refuses the AQI dashboard (gauge, giant number, pollutant tiles), the bright card-stack wellness app, and the road-sign boards this system replaced. The air's severity is said in words, never shouted in colour.

**Key Characteristics:**
- Paper and ink, five time-of-day phases, six haze levels, all AA-tested.
- One deep green for actions and people; a slate blue only for the home.
- Newsreader for what matters, Hanken Grotesk for text, JetBrains Mono only for measurements.
- Hairlines and tone instead of shadows; 10px and 14px corners.
- A softened sky band under the top bar on Today, drawn from real sun, cloud and rain.

## Colors

Warm paper and ink in five phases, one green, one slate blue, and CPCB colour kept to a swatch.

### Primary
- **Ledger Green** (`accent`; `accent-evening` at evening, `accent-dark` at dusk and night): every action (buttons, the primary link button, selection, focus ring, caret, form accent) and every person's step (rail dot, the name under the step). Its 14% mix into the panel (`--accent-tint`) rings the next-step dot and backs the sample-household tag.

### Secondary
- **Slate Home Blue** (`home` and its phase variants): only steps about the home, on the dot and the step's "who" line.

### Tertiary
- **Calm Amber** (`warn` and variants): the standard-advice label and form errors, always as a 14% tint (`--warn-tint`) with an amber-edged border, and the hatched worst hour on the 24-hour strip. Text on it stays ink.

### Neutral
- **Phase Paper** (`<phase>-sky`): the page ground. The rendered ground is `--ground`, smog mixed into it at the haze percentage (0, 4, 7, 10, 14, 18%).
- **Bar Paper** (`<phase>-bar-sky`): the top bar, hazed the same way (`--bar`).
- **Panel Paper** (`<phase>-panel`): side panels, form groups, fact labels, the numbers behind a step.
- **Ink / Muted Ink** (`<phase>-ink`, `<phase>-muted`): text and secondary text.
- **Hairline** (`<phase>-line`): every divider, border and the rail itself.
- **Smog** (`<phase>-smog`): never painted directly; only mixed into the paper and laid over the sky as the haze veil.
- **High Sky** (`<phase>-sky-high`): the top of the sky band, mixed 62% into the ground.

### Band and kind colours
- **CPCB bands** (`band-*`): the official AQI band colours, used only as the band swatch.
- **Fact kinds** (`kind-*`): a 6px dot inside each fact label (measured, forecast, estimate, guidance, household); the word is the label. `kind-measured` is also the live dot in the top bar.

### Named Rules
**The Swatch-Only Rule.** A CPCB band colour appears only as an 11px swatch beside the band's name. Never as a fill, a text colour, a border or a background.

**The One Green Rule.** Green carries every action and every person's step; blue marks only the home. No third accent.

**The Every-Phase Contrast Rule.** `tests/test_contrast.py` checks ink, muted, accent and home against sky and bar-sky at all six haze levels in all five phases, and against panel; on-accent on accent; and that the dark-mode block equals the night palette. Any new text colour or ground goes into that test before it ships.

## Typography

**Display Font:** Newsreader 500 (with Noto Serif Devanagari, Georgia)
**Body Font:** Hanken Grotesk variable (with Noto Sans, Noto Sans Devanagari, system-ui)
**Label/Mono Font:** JetBrains Mono variable (with ui-monospace)

**Character:** A book serif sets what a parent reads first; a plain grotesk carries everything else; mono marks a number as a measurement. All three are self-hosted woff2 with latin and latin-ext subsets; Devanagari falls back to the system's Noto faces for the Hindi plan. Numerals are tabular throughout.

### Hierarchy
- **Display** (`display`): the start page headline, 16ch max.
- **Headline** (`headline`): the place name on Today.
- **Title, next step** (`title-next`): the next step on the rail, the one large step of the day.
- **Title** (`title`): section headings (1.25rem in the side column); the weekly totals use the serif at 1.75rem and Ask answers at 1.25rem.
- **Step** (`step`): every other step's action. Why-lines are 0.9375rem muted, 62ch max.
- **Body** (`body`): 16px/1.55; intro copy at 1.0625rem, 54ch max.
- **Label** (`label`): fact labels; group heads ("Next", "Later today") are 0.8125rem 500 muted sans.
- **Figure** (`figure`): step figures right-aligned; fact figures 0.9375rem; station line, times and the live pill 0.75 to 0.8125rem.

### Named Rules
**The Mono-Is-Measurement Rule.** JetBrains Mono only for measured or computed values and their sources: station and distance, times, µg/m³, kg, hour ticks, model and prompt identifiers. Never for prose or headings.

**The Serif-For-What-Matters Rule.** Newsreader only at 500 and only for headings, the place, the next step, an answer and the weekly totals. Body text is never serif.

## Layout

A centred page up to 1440px with 24px side padding, a 4/8/12/16/24/32/48px spacing scale, and hairline-separated rows rather than cards.

- **Today, phone:** one column: place and air line, the plan rail, the side panels, home, trips, the week.
- **Today, from 960px:** a 7:5 grid with 48px column gap. The plan, home, trips and week stay in the left 7 columns at every desktop width; the right 5 columns (24-hour strip, what the air means, Ask, how the plan was made) are sticky and scroll on their own.
- **Start, from 1100px:** a 5:7 grid; the intro and how-it-works rail stay sticky on the left, samples and the household form on the right.
- **Sky band:** 64px tall on phones, `clamp(96px, 6.8vw, 132px)` from 960px; a narrower drawing below 720px so the sun near sunrise or sunset is not cropped.
- Measures: 46 to 72ch for running text; rows let the figure sit at the right edge.

## Elevation & Depth

Flat. Depth is tone and hairline: panel paper on page paper with a 1px line. The only box-shadows are flat rings, never offsets: the live dot's 3px halo and the next-step dot's 5px tint ring.

### Named Rules
**The Paper-on-Paper Rule.** No drop shadows, glass or blur. A surface lifts by being panel paper with a hairline edge.

## Shapes

Gently rounded: 10px on controls, inputs, notes and the numbers behind a step; 14px on side panels and form groups; full pills for fact labels, the live status and the sample tag. Small marks stay small: 3px swatch corners, 2px hour cells, 4px on the now-pin and focus ring. Circles are the rail's language: 13px outlined dots, the 15px filled next dot, 21px numbered rings on the start page. Chevrons are drawn (an SVG stroke, or a rotated 1.5px border corner on disclosures), never glyphs.

## Components

### Buttons
- **Shape:** gently rounded (10px), 44px minimum height.
- **Primary:** Ledger Green with on-accent text, 600 weight, 10px 18px; the start page's link button is the same at 12px 20px. One primary per view.
- **Hover / Focus:** hover mixes 14% ink into the green; active nudges down 1px; focus is a 2px green outline at 3px offset. Transitions 160ms on the house ease (`cubic-bezier(0.16, 1, 0.3, 1)`).
- **Quiet:** transparent with a hairline border; hover shows panel paper and a muted border. Pressed (`aria-pressed="true"`) inverts to ink on paper, used for "I did this" and the colour choice.

### Chips (fact labels)
- **Style:** panel paper pill with a hairline border, muted 11px label, and a 6px kind dot before the word. Sits beside headings and before each fact.

### Cards / Containers
- **Side panels:** panel paper, 14px corners, hairline border, 16px 24px 24px padding. How-the-plan-was-made is a quiet disclosure row, not a card.
- **Form groups:** the same paper and corner, with a serif legend.
- **Notes:** panel paper, 10px corners, 8px 12px.

### Inputs / Fields
- **Style:** panel paper, hairline border, 10px corners, 10px 12px, 44px high; the Ask input sits on the page paper inside its panel.
- **Hover:** border darkens to muted. **Focus:** the global green outline. **Error:** the amber-tint error block above the form.

### Navigation
- **Top bar:** bar paper with a hairline under it. The serif wordmark "Nirmal" in ink with "Air" in green, and a mono live pill (hairline border, measured-green dot): "AQI n" in ink and the measured time on Today, "Live CPCB data" on start.
- **Footer:** hairline above, muted 13px source line, ink links.

### Day Rail (signature)
Each step is a three-column row: a 20px rail column, the text, and a right-edge mono figure. The 1px hairline runs between dot centres with no loose ends. Person dots are outlined green, home dots outlined blue, on the page paper. The next step fills its dot, adds the tint ring and sets the action in `title-next`. "The numbers behind this" opens a panel-paper list of labelled facts. While the plan is written, the rail's shape pulses gently (opacity to 0.45).

### Air Line
The place's AQI in 1.125rem 600 beside the band name and its swatch, then the mono station line. It is never larger than the place name.

### 24-Hour Strip
24 cells, 16px high, 2px apart and 2px rounded: neutral ink at 12%, cleaner hours green at 32%, dirtier amber at 32%, the cleanest hour solid green, the worst hour an amber hatch. An ink "Now" pin sits over the first hour; mono ticks below; a legend names the cleanest and worst hours in words.

### Sky Band
Under the top bar on Today only, aria-hidden and carrying no text. Its top stop mixes the phase's high sky 62% into the paper; its lower 55% fades into the paper so it has no edge. Sun or moon sit on the real path for the place, and stars, clouds and rain come from real data, all positioned by `app/domain/scene.py`. Smog lays a veil over it (opacity 0.06 to 0.25 by haze) and hides stars. Motion plays once on arrival (the body rises over 1.6s, clouds drift in over 1.8s), then only clouds float, stars twinkle and rain falls.

## Do's and Don'ts

### Do:
- **Do** set every colour on `<html data-phase data-haze>` and add any new text colour or ground to `tests/test_contrast.py` (The Every-Phase Contrast Rule).
- **Do** say the band in words with its 11px swatch beside it (The Swatch-Only Rule).
- **Do** give each step a named person, a why-line and, when there is one, a mono figure at the right edge.
- **Do** label every fact with its kind (measured, forecast, estimate, guidance, household).
- **Do** stop all transitions and animations under `prefers-reduced-motion: reduce`, including the sky.
- **Do** keep sun, moon, stars, clouds and rain driven by `app/domain/scene.py`, never placed by hand.

### Don't:
- **Don't** add a gauge, a dial or a giant AQI number; the place name stays the largest text on Today.
- **Don't** use alarm styling: no red, no warning icons, no flashing. Amber appears only as a tint, a border or the worst-hour hatch.
- **Don't** fill, tint or colour text with a CPCB band colour.
- **Don't** add drop shadows, glass, blur or decorative gradients; the sky band and the worst-hour hatch are the only gradients.
- **Don't** bring back boards or sign plates; steps are rows on the rail and facts are rows between hairlines.
- **Don't** use mono for prose or the serif for body text.
- **Don't** put text in the sky band.
