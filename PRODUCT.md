# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary: a parent in an Indian city during winter smog, checking on their phone in the morning (around 7 am), before the school run and the commute, deciding for the whole household: windows, a child's outdoor play, a grandparent's walk, how someone gets to work. Households mix adults, children, seniors and people with asthma or heart conditions, who need different advice.

Secondary: PromptWars evaluators, who try the app on a laptop with the sample households and judge it as if they were that family.

## Product Purpose

NirmalAir tells each household, from today's measured air, what to do and why. It reads the nearest CPCB station's official AQI, ranks the day's hours with a forecast, and turns the household's profile into a morning-to-evening plan: routines moved or kept, indoor steps, and lower-emission commute swaps, each with the direct impact worked out in code. Success: a parent knows in seconds what their family does today, and can see the numbers behind every step.

## Positioning

"AI explains, code calculates, real data decides." Every number on screen comes from a CPCB measurement or tested code (indoor estimates, cigarette equivalent, CO₂ and exposure of each commute swap); the AI only explains, and a number guard rejects any figure the AI invents. Decisions such as "Dadi's walk moves indoors" are made by rules from CPCB's bands. Every AI answer shows how it was generated. AQI sites show a number; NirmalAir gives a named person a step and its consequence.

## Operating Context

- Used outdoors-minded, mornings, one-handed on a phone; repeat daily through the smog season (October to February).
- Works anywhere in India by place search (older names like Bangalore and Gurgaon work) or browser location.
- Evaluators use sample households and watch for real-time data, source and timestamp, personalisation (a commuter and a family with kids get different advice) and visible AI provenance.

## Capabilities and Constraints

- Stack: FastAPI, Jinja templates, htmx; no React. Hosted on Vercel (Mumbai). Strict CSP: no inline scripts or styles, no third-party scripts.
- Data: CPCB via data.gov.in (measured, hourly, station name, distance and "measured at" time always shown); Open-Meteo forecast only to rank hours, labelled forecast; estimates labelled estimate.
- Household profile and a 7-day log live in a signed cookie; no accounts.
- AI chain Groq → Gemini → labelled "Standard advice (not AI-generated)". Hindi output for the AI text is planned; the interface stays English.
- States the screen must handle: loading, unknown place, nearest station far away, station not reporting, AI unavailable, off-topic question.
- Not offered: medical advice, product sales, indoor sensor readings.

## Brand Commitments

- Name: NirmalAir ("nirmal" = clean, pure).
- Must not feel like: an AQI-site clone (giant number, gauge, pollutant tiles); alarmist doom (red warnings, smoke imagery, scary wording); the generic AI look (gradients, glass cards, emoji icon tiles, the Stitch "Aura" style); clinical or childish (hospital report, mascots, badges, points).
- Voice: calm, plain, specific; a sensible friend telling the family what to do today.

## Evidence on Hand

- Live CPCB readings and real AI plans from test runs (e.g. ITO Delhi, AQI 326 Very Poor, 24 Nov 2026).
- Sources for every estimate in `nirmal-air/docs/ASSUMPTIONS.md`.
- No users, testimonials or usage numbers exist; none may be invented.

## Product Principles

1. Decisions first, numbers as their reasons.
2. Every number shows where it came from: measured, forecast, estimate or your household.
3. Calm under bad air: clear steps, never fear.
4. Personal: each step names who it is for.
5. Honest trade-offs: a lower-CO₂ swap that means breathing more polluted air says so.

## Accessibility & Inclusion

WCAG 2.2 AA: contrast, keyboard use, screen-reader labels, live regions for htmx updates, reduced motion respected. AQI colour is never the only signal; the band name always appears in text. Readable in bright morning light on a phone.
