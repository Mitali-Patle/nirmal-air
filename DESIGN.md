---
name: NirmalAir
description: Today's measured air, set out as road signs for each person at home, on a ground painted by the local sky.
colors:
  sign-green: "#0A6B3D"
  sign-green-deep: "#08542F"
  sign-blue: "#1D4F91"
  sign-blue-deep: "#173F74"
  sign-yellow: "#F2C230"
  sign-legend: "#FFFFFF"
  on-yellow: "#1B2220"
  band-good: "#00A650"
  band-satisfactory: "#8FC93A"
  band-moderate: "#F5D90A"
  band-poor: "#F28C1C"
  band-very-poor: "#E02424"
  band-severe: "#8E1616"
  kind-measured-bg: "#DDEFE4"
  kind-measured-fg: "#0A5130"
  kind-forecast-bg: "#DEE8F5"
  kind-forecast-fg: "#173F74"
  kind-estimate-bg: "#F5E8C8"
  kind-estimate-fg: "#5C4100"
  kind-guidance-bg: "#E6E9E6"
  kind-guidance-fg: "#2E3A34"
  kind-household-bg: "#ECE4F3"
  kind-household-fg: "#46306A"
  route-dirtier: "#7A4A2A"
  route-worst: "#6E2E22"
  morning-sky: "#F3F6F4"
  morning-bar-sky: "#FFFFFF"
  morning-smog: "#B8AD99"
  morning-ink: "#1B2220"
  morning-muted: "#3E4944"
  morning-panel: "#FFFFFF"
  morning-line: "#CDD5D0"
  afternoon-sky: "#F7F0D4"
  afternoon-bar-sky: "#FFFBEA"
  afternoon-smog: "#B5A991"
  afternoon-ink: "#1F2220"
  afternoon-muted: "#403F36"
  afternoon-panel: "#FFFDF6"
  afternoon-line: "#DED3B2"
  evening-sky: "#EBD6A8"
  evening-bar-sky: "#F5E6C3"
  evening-smog: "#A79A84"
  evening-ink: "#221E16"
  evening-muted: "#3E3829"
  evening-panel: "#FBF5E8"
  evening-line: "#D6C296"
  dusk-sky: "#1E3354"
  dusk-bar-sky: "#172A47"
  dusk-smog: "#3E3B38"
  dusk-ink: "#EEF1F5"
  dusk-muted: "#BAC5D2"
  dusk-panel: "#24395C"
  dusk-line: "#3D5579"
  night-sky: "#15181A"
  night-bar-sky: "#101314"
  night-smog: "#302D2A"
  night-ink: "#ECEFEC"
  night-muted: "#B4BCB7"
  night-panel: "#1F2427"
  night-line: "#383F43"
typography:
  display:
    fontFamily: "Overpass, Noto Sans, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "clamp(1.75rem, 5vw, 2.75rem)"
    fontWeight: 800
    lineHeight: 1.08
    letterSpacing: "-0.025em"
  sign-next:
    fontFamily: "Overpass, Noto Sans, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "clamp(1.75rem, 6.5vw, 2.375rem)"
    fontWeight: 800
    lineHeight: 1.04
    letterSpacing: "-0.02em"
  section-title:
    fontFamily: "Overpass, Noto Sans, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  aqi-figure:
    fontFamily: "Overpass, Noto Sans, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.01em"
    fontFeature: "tnum"
  title:
    fontFamily: "Overpass, Noto Sans, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 800
    lineHeight: 1.15
  sign-title:
    fontFamily: "Overpass, Noto Sans, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "1.1875rem"
    fontWeight: 800
    lineHeight: 1.15
  figure:
    fontFamily: "Overpass, Noto Sans, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 800
    fontFeature: "tnum"
  lead:
    fontFamily: "Overpass, Noto Sans, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.5
  body:
    fontFamily: "Overpass, Noto Sans, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: "tnum"
  body-small:
    fontFamily: "Overpass, Noto Sans, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.4
  label:
    fontFamily: "Overpass, Noto Sans, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
  caption:
    fontFamily: "Overpass, Noto Sans, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
  chip:
    fontFamily: "Overpass, Noto Sans, Noto Sans Devanagari, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 700
    lineHeight: 1.5
  mono:
    fontFamily: "ui-monospace, Cascadia Mono, Roboto Mono, monospace"
    fontSize: "0.8125rem"
rounded:
  board: "12px"
  board-inner: "8px"
  control: "8px"
  track: "7px"
  chip: "4px"
  swatch: "3px"
spacing:
  space-1: "4px"
  space-2: "8px"
  space-3: "12px"
  space-4: "16px"
  space-5: "24px"
  space-6: "32px"
  space-7: "48px"
components:
  sign-step:
    backgroundColor: "{colors.sign-green}"
    textColor: "{colors.sign-legend}"
    typography: "{typography.sign-title}"
    rounded: "{rounded.board}"
    padding: "5px"
  sign-next:
    backgroundColor: "{colors.sign-green}"
    textColor: "{colors.sign-legend}"
    typography: "{typography.sign-next}"
    rounded: "{rounded.board}"
    padding: "5px"
  sign-home:
    backgroundColor: "{colors.sign-blue}"
    textColor: "{colors.sign-legend}"
    typography: "{typography.sign-title}"
    rounded: "{rounded.board}"
    padding: "5px"
  sign-plate-open:
    backgroundColor: "{colors.sign-legend}"
    textColor: "{colors.on-yellow}"
    typography: "{typography.body-small}"
    rounded: "{rounded.board-inner}"
  sample-household:
    backgroundColor: "{colors.sign-blue}"
    textColor: "{colors.sign-legend}"
    typography: "{typography.title}"
    rounded: "{rounded.board}"
    padding: "5px"
  sample-household-hover:
    backgroundColor: "{colors.sign-blue-deep}"
  sample-tag:
    backgroundColor: "{colors.sign-yellow}"
    textColor: "{colors.on-yellow}"
    typography: "{typography.caption}"
    rounded: "{rounded.chip}"
    padding: "1px 8px"
  standard-advice-label:
    backgroundColor: "{colors.sign-yellow}"
    textColor: "{colors.on-yellow}"
    typography: "{typography.body-small}"
    rounded: "{rounded.control}"
    padding: "8px 12px"
  button-primary:
    backgroundColor: "{colors.sign-green}"
    textColor: "{colors.sign-legend}"
    rounded: "{rounded.control}"
    padding: "10px 18px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.sign-green-deep}"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.morning-ink}"
    rounded: "{rounded.control}"
    padding: "10px 18px"
    height: "44px"
  button-pressed:
    backgroundColor: "{colors.morning-ink}"
    textColor: "{colors.morning-sky}"
    rounded: "{rounded.control}"
  input:
    backgroundColor: "{colors.morning-panel}"
    textColor: "{colors.morning-ink}"
    rounded: "{rounded.control}"
    padding: "10px 12px"
    height: "44px"
  panel:
    backgroundColor: "{colors.morning-panel}"
    textColor: "{colors.morning-ink}"
    rounded: "{rounded.board}"
    padding: "16px"
  distance-plate-row:
    textColor: "{colors.morning-ink}"
    typography: "{typography.body}"
    padding: "12px 0"
  chip-measured:
    backgroundColor: "{colors.kind-measured-bg}"
    textColor: "{colors.kind-measured-fg}"
    typography: "{typography.chip}"
    rounded: "{rounded.chip}"
    padding: "0 6px"
  chip-forecast:
    backgroundColor: "{colors.kind-forecast-bg}"
    textColor: "{colors.kind-forecast-fg}"
    typography: "{typography.chip}"
    rounded: "{rounded.chip}"
    padding: "0 6px"
  chip-estimate:
    backgroundColor: "{colors.kind-estimate-bg}"
    textColor: "{colors.kind-estimate-fg}"
    typography: "{typography.chip}"
    rounded: "{rounded.chip}"
    padding: "0 6px"
  chip-guidance:
    backgroundColor: "{colors.kind-guidance-bg}"
    textColor: "{colors.kind-guidance-fg}"
    typography: "{typography.chip}"
    rounded: "{rounded.chip}"
    padding: "0 6px"
  chip-household:
    backgroundColor: "{colors.kind-household-bg}"
    textColor: "{colors.kind-household-fg}"
    typography: "{typography.chip}"
    rounded: "{rounded.chip}"
    padding: "0 6px"
  now-pin:
    backgroundColor: "{colors.morning-ink}"
    textColor: "{colors.morning-panel}"
    typography: "{typography.chip}"
    rounded: "{rounded.chip}"
    padding: "0 6px"
  band-swatch:
    rounded: "{rounded.swatch}"
    size: "13px"
  route-track:
    rounded: "{rounded.track}"
    height: "14px"
  hour-cleanest:
    backgroundColor: "{colors.sign-green}"
    height: "14px"
---

# Design System: NirmalAir

## Overview

**Creative North Star: "Road Signs Under Today's Sky"**

NirmalAir sets out a household's day as a short run of Indian road signs, one per decision: who it is for, what to do, and the figure that step changes, right-aligned like a distance. The signs sit on a ground that is the actual sky at the household's place: one of five phases computed from sunrise and sunset, dulled toward smog by the measured CPCB AQI band. Air quality changes the ground; it never changes the signs.

The world is calm and plain. The measured air sits in the top bar as a single air line. Enamel boards carry the decisions. Home and travel estimates are distance plates set straight on the ground: a heavy rule, rows, figures on the right. The side column (the 24-hour route line, what the air means, Ask, how the plan was generated) sits in quiet bordered panels in the sky's own tones. Every number is labelled with the kind of number it is. There is no gauge, no giant AQI number, no pollutant tiles, no red warning styling, and no decorative gradient, glass or emoji. All styling lives in four stylesheets because the CSP forbids inline styles and scripts.

**Key Characteristics:**
- Signs keep fixed road-sign colours in every phase and haze level: green for steps people take, blue for the home, yellow for "standard advice, not AI-generated" and the sample-household tag.
- The page ground and top bar follow the local sky and are hazed by the measured AQI band.
- One typeface (Overpass), heavy legends, tabular figures.
- Every number is labelled measured, forecast, estimate, CPCB guidance or your household.
- WCAG AA is enforced in tests for every phase and haze combination.

## Colors

Fixed enamel sign colours over a moving sky ground; band and fact-kind colours appear only at chip, swatch and route-line size.

### Primary
- **Enamel Green** (sign-green): the board for every step a person takes, the primary button, the start page's main link, the cleanest hours on the route line and its key, text selection, and the form accent colour. Its deeper shade (sign-green-deep) is the hover state.
- **Enamel Blue** (sign-blue): the board for steps about the home (purifier, windows) and the sample-household buttons on the start page. Hover deepens to sign-blue-deep.
- **Sign White** (sign-legend): every legend, the inner border on green and blue boards, and the open supplementary plate under a sign.

### Secondary
- **Road-works Yellow** (sign-yellow): the label on any plan or answer that came from fixed rules rather than an AI model, the sample-household tag in the top bar, the skip link, and the focus ring.
- **Sign Black** (on-yellow): the fixed dark legend on yellow, and the text on the open white plate. It does not follow the phase, so yellow and white surfaces read the same at night.

### Tertiary
- **CPCB band colours** (band-good through band-severe): CPCB's official AQI band colours, used only as a 13px swatch beside the band name.
- **Fact-kind chips** (kind-*-bg / kind-*-fg): five pale tinted pairs, one per kind of fact: Measured (green), Forecast (blue), Estimate (ochre), CPCB guidance (grey-green), Your household (violet). They keep the same light values in dark phases.
- **Route browns** (route-dirtier, route-worst): hours dirtier than usual on the route line (a 38% mix into the panel) and the hatched worst window.

### Neutral (the sky ground, per phase)
Each phase defines sky, bar-sky (the top bar, a step lighter), smog, ink, muted, panel and line. The phase is set server-side on `<html data-phase>`: morning (sunrise to 11 am, near-white), afternoon (pale yellow), evening (last two hours before sunset, muted gold), dusk (sunset to 9 pm, deep blue) and night (asphalt). The visitor's "Light" choice swaps dusk and night for morning; "Dark" always uses night; "Follow the sky" also uses the night values when the phone is set to dark mode.

The haze: `data-haze` 0 to 5 is the measured band's position on CPCB's scale (0 when nothing was measured), giving 0, 8, 15, 22, 30 or 38% of the phase's smog colour mixed into sky and bar-sky (`color-mix(in srgb, …)`). Panels are not hazed.

### Named Rules
**The Fixed Signs Rule.** Sign colours never change with phase, haze or theme. Only the ground moves.

**The Swatch-Only Rule.** CPCB band colours appear only as the small swatch beside the band's name, never as a board, background, border or text colour. The band name is always written out, so colour is never the only signal.

**The Tested Ground Rule.** `tests/test_contrast.py` reads `tokens.css` and requires 4.5:1 for ink and muted text on sky and bar-sky at all six haze levels in all five phases, for ink and muted on panels, for the legend on all four boards, and for every chip pair. Change a colour and the test together.

## Typography

**Display Font:** Overpass (variable, 100 to 900, self-hosted latin and latin-ext WOFF2), with Noto Sans, Noto Sans Devanagari and system-ui
**Label/Mono Font:** ui-monospace, only for fact IDs and the raw model reply in "How this was generated"

**Character:** Overpass is a highway-sign sans; set at 800 it reads like a sign legend, and at 400 it is plain, friendly body text. Figures are tabular across the whole page.

### Hierarchy
- **Display** (800, clamp 1.75 to 2.75rem, 1.08): the start page's one-line promise, max 22ch.
- **Sign next** (800, clamp 1.75 to 2.375rem, 1.04): the action on the large next-step board, with the drawn arrow at its right edge.
- **Section title** (800, 1.375rem): section headings on the Today page, each followed by its kind chip where one applies. The plan's own heading is visually hidden.
- **AQI figure** (800, 1.375rem, 1): "AQI 283" in the top bar. Deliberately modest.
- **Title** (800, 1.25rem, 1.15): sample-household names and section headings on the start page.
- **Sign title** (800, 1.1875rem, 1.15): the action on each smaller board.
- **Figure** (800, 1.0625rem, no wrap): the right-edge figure on a smaller sign; 1.125rem in distance plates; 1.375rem on the next-step board.
- **Lead** (600, 16px, muted, max 62ch): the plan's one-sentence summary above the boards.
- **Body** (400, 16px, 1.5): running text; distance-plate rows cap at 62ch.
- **Body small** (400, 0.9375rem, 1.4): the reason on a sign or plate, notes, the route legend, the "Later today" group heading (at 800, muted).
- **Label** (600, 0.875rem): form labels and the plate's summary line.
- **Caption** (0.8125rem): the who and when line on a smaller sign (600, slightly translucent; 0.9375rem on the next-step board), the air source line, the sample tag (700), the sky note and footnotes.
- **Chip** (700, 0.75rem): fact-kind chips and the Now pin (800).

### Named Rules
**The One Face Rule.** Overpass carries everything; hierarchy comes from weight (800 against 400) and size, not from a second family.

**The Distance Figure Rule.** A figure sits at the right edge of its sign or plate row, bold, unwrapped and tabular, the way a road sign gives distances.

## Layout

The top bar runs the full width (content max 1160px, 12px 16px padding): brand and place on the first row, the measured air line on its own row below on every width. On phones the source text takes a further row; from 960px it sits inline after the band.

Phones get one column inside a 16px gutter, sections 32px apart, in reading order: plan, side column (route, what this air means, Ask, how this was generated), At home, Getting around. From 960px the Today page is a 7:5 grid (max width 1160px, 32px gaps, 32px top padding). The left column holds the plan, At home and Getting around. The right column is one aside that is sticky 16px from the top, capped at the viewport height minus 32px, and scrolls on its own (`overscroll-behavior: contain`); its panels are 16px apart. "How this was generated" arrives in the aside's slot with the plan, by an htmx out-of-band swap.

The start page is a single 880px column with 48px between sections. Spacing follows a 4px base (space-1 to space-7: 4, 8, 12, 16, 24, 32, 48). Touch targets are at least 44px for buttons and fields, 36px for the theme toggles and place choices.

## Elevation & Depth

Flat. There are no drop shadows. Depth comes from contrast between the saturated boards and the pale or dark sky, from panels separated by a 1px line border, and from the 2px ink rule on distance plates. The only box-shadow is the focus ring's 5px ink halo around a 3px yellow outline.

Motion is small: buttons change colour over 160ms on `cubic-bezier(0.16, 1, 0.3, 1)` and press down 1px; placeholder boards fade between 45% and 25% opacity while the plan loads. Reduced-motion settings remove both.

### Named Rules
**The Flat Enamel Rule.** Boards, plates and panels sit flat on the ground. Prominence comes from colour and size, never from lift.

## Shapes

Gently rounded rectangles throughout. A sign is a 12px-radius board with 5px of board colour around a 2px white inner border at 8px radius (3px border on the next-step board), so the white line follows the outer corner. The open plate, controls, notes and the yellow label use 8px; chips, the sample tag and the Now pin 4px; the band swatch 3px with a thin ink-tinted edge; the route line is one continuous 7px-radius track. Distance plates have no corners: a 2px ink rule on top and 1px line dividers. The drawn shapes are the arrow on the next-step board (round caps, stroke 3.5) and the Now pin's small downward pointer; the favicon is the same green board and arrow.

## Components

### Sign boards
The signature component: one board per step.
- **Smaller sign:** who and when (caption), then one row with the action on the left and the figure on the right. Nothing else on the board.
- **Next step:** the first sign is larger, with a 3px inner border, the action at sign-next size with a drawn arrow at its right edge, then a thin white rule and a row with the reason on the left and the figure (1.375rem) on the right. The reason stays on this board.
- **Step (green) / Home (blue):** fixed colours, white legend.
- **Supplementary plate:** a disclosure inside the board's outer frame, under the bordered legend. Closed, it is an underlined white summary line on the board colour ("Why, and the numbers" on smaller signs, "The numbers behind this" on the next step). Open, it becomes a white 8px plate with Sign Black text: the reason (smaller signs only), then each fact with its kind chip.
- **Grouping:** a muted lead sentence, the next step, then "Later today", then a collapsed "Earlier today".
- **Loading:** empty green and blue placeholder boards at reduced opacity, hidden from screen readers; a status line announces when the plan is ready.

### Air line (top bar)
"AQI" and the number, then the band swatch and band name in bold, then "Measured [time] at [station], [distance] away · CPCB via data.gov.in" in muted caption. With no recent station reading, only the muted sentence saying so. The air line takes the bar's haze; it has no panel.

### Distance plates (At home, Getting around)
Estimates set like a distance plate, directly on the ground: the section title carries one Estimate chip, then a 2px ink rule, then rows divided by 1px lines, each with the text on the left (body) and the figure on the right (800, 1.125rem, no wrap), 12px vertical padding. A muted caption footnote may follow.

### Route line
The next 24 hours as one continuous track, 14px tall with 7px rounded ends and no gaps, starting at the current hour; a "Now" pin (ink chip with panel-coloured text and a small pointer) sits above its left end. Neutral hours are a 14% ink tint of the panel; cleaner hours a 30% green mix; dirtier hours a 38% route-dirtier mix; the cleanest window solid Enamel Green; the worst window a 135° route-worst hatch. Hour ticks run below in muted chip-size text. The track is hidden from screen readers; a text legend with matching keys states the cleanest and worst windows. The panel heading carries a Forecast chip.

### What this air means
A side panel headed with a CPCB guidance chip: the band name and CPCB's health statement, then notes for a last-known reading, a distant station or no station, then a muted caption naming the sky phase and haze the page shows.

### Buttons
- **Shape:** gently rounded (8px), at least 44px tall.
- **Primary:** Enamel Green with white text, bold; hover deepens to sign-green-deep, active presses 1px.
- **Quiet:** transparent with a line border; hover darkens the border to muted.
- **Pressed toggle:** ink fill with ground-coloured text (the theme switch).
- **Sample household:** a whole blue board as a button: name, place and summary inside the white inner border.

### Chips
- **Style:** pale tinted fill, dark text of the same hue, 4px radius, 700 at 0.75rem, no border.
- **Use:** before each fact in plates and answers, or once in a section heading when every number in that section is the same kind (Forecast, CPCB guidance, Estimate).

### Tags
- **Sample household:** a yellow 4px tag with Sign Black text after the place in the top bar, "Sample household: [name]", shown only for a sample.
- **Standard-advice label:** a yellow 8px strip with Sign Black text above any plan or answer that came from fixed rules: "Standard advice (not AI-generated)".

### Cards / Containers
- **Corner Style:** 12px, matching the boards.
- **Background:** the phase's panel colour with a 1px line border, 16px padding. Used for the side-column panels and the start page's form groups.
- **Shadow Strategy:** none (see Elevation & Depth).
- **Notes:** smaller 8px-radius bordered panels for caveats (station far away, last reading, forecast unavailable).

### How this was generated
A disclosure panel in the side column: who wrote the plan, prompt version and time as a definition list, then h3 subheads (0.875rem) for attempts, the facts sent to the model (fact IDs in mono), the question and the raw model reply in an 8px ink-tinted box that scrolls past 18rem. Inside an answer it appears without its panel border.

### Inputs / Fields
- **Style:** panel fill, 1.5px line border, 8px radius, 10px 12px padding, 44px tall; placeholder in muted.
- **Hover:** border darkens to muted.
- **Focus:** the shared focus ring, 3px yellow outline with a 5px ink halo.
- **Error:** a 2px ink-bordered panel listing the problems above the form, announced as an alert.

### Navigation
The top bar in bar-sky (hazed like the ground) with a 1px line under it: NirmalAir at 800 on the left; on Today, the place, a "Change" link and the sample tag, then the air line. The footer carries data sources, links to edit the household or switch the plan's language, and the colours choice (Follow the sky, Light, Dark).

## Do's and Don'ts

### Do:
- **Do** put every plan step on a board: green for what a person does, blue for the home, white legend inside a 2px white inner border.
- **Do** keep smaller signs to who, the action and the figure; put the reason and the facts in the supplementary plate. Only the next-step board shows its reason.
- **Do** name who each sign is for and when, and put its figure at the right edge (The Distance Figure Rule).
- **Do** label every number with its kind: a chip on each fact, or one chip in the section heading when the whole section is one kind.
- **Do** show the measured air in the top bar: the AQI number, the 13px band swatch with the band's written name, then measured time, station, distance and source.
- **Do** set estimate lists as distance plates on the ground: 2px ink rule, 1px row dividers, figures right-aligned.
- **Do** mark any plan or answer not written by an AI model with the yellow standard-advice label, and a sample household with the yellow sample tag.
- **Do** set phase and haze only through `data-phase` and `data-haze` on `<html>`, and update `tests/test_contrast.py` with any colour change.
- **Do** keep every style in the stylesheets and every colour in `tokens.css`; the CSP blocks inline styles.

### Don't:
- **Don't** use CPCB band colours for boards, backgrounds, borders or text (The Swatch-Only Rule).
- **Don't** recolour signs by phase, haze or theme; bad air dulls the ground, never the signs (The Fixed Signs Rule).
- **Don't** use red warning styling, alarm wording or smoke imagery for bad air.
- **Don't** build an AQI dashboard: no gauge, no giant AQI number, no pollutant tiles.
- **Don't** use decorative gradients, glass, drop shadows, emoji or icon fonts. The hatched worst-hours fill is a data encoding with a text legend, not decoration.
- **Don't** add a second typeface for display or body.
