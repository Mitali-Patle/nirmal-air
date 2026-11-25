# NirmalAir

**Today's measured air, turned into a plan for each person at home.**

NirmalAir is a GenAI clean-air assistant for Indian families living through winter smog. It
reads the official air quality at the nearest CPCB monitoring station and tells each household
what to do today and when: who should move their walk indoors, when to open the windows, which
commute swap saves CO₂. It also says what each choice changes, with numbers worked out in code
rather than by the AI.

**Live app:** https://nirmal-air.vercel.app

| | |
|---|---|
| Product brief | [PRODUCT.md](PRODUCT.md) |
| Design system | [DESIGN.md](DESIGN.md) |
| Every constant and its source | [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md) |

## Chosen vertical

**Urban Air Quality Assistant.** The brief: help families and communities through winter smog
with low-emission daily routines, indoor air-quality steps and sustainable alternatives, suited
to their location and lifestyle, and explain the direct impact of each choice.

| What the brief asks for | Where NirmalAir does it |
|---|---|
| Low-emission daily routines | The plan's signs for each person's routine, plus the cleanest and worst hours |
| Indoor air-quality steps | The windows rule, purifier and indoor-source steps, and indoor PM2.5 estimates |
| Sustainable alternatives | Commute swaps (bus, metro, cycle, walk, carpool) with CO₂ saved per week |
| Location | The nearest CPCB station to any Indian place, and the sky colour of that place |
| Lifestyle | Household members, sensitivities, routines, commutes and home |
| Direct impact of each choice | A figure on every sign, the facts behind it one tap away, and a "This week" log that adds up what the household actually did |

## Approach and logic

**AI explains, code calculates, real data decides.**

1. **Real data decides.** The air quality comes only from CPCB's real-time feed, from the
   nearest station that has a valid reading under 3 hours old. Its station, distance, time and
   source are always on screen. The forecast is used only to rank hours against each other.
2. **Code calculates.** Every number is computed by tested code: the AQI and its band, PM2.5,
   indoor estimates, cigarette equivalents, commute CO₂ and the polluted air breathed on the
   way. Code also makes the decisions: whether a routine moves indoors or to the cleanest
   time, the windows rule, and which swap to offer. Someone with a heart or lung condition is
   never offered a swap that makes them breathe more polluted air.
3. **AI explains.** The model receives a **facts bundle**: short sentences written by code,
   each with an id and a label (measured, forecast, estimate, CPCB guidance, your household).
   It writes the plan as JSON, citing fact ids. A **number guard** rejects any number the AI
   writes that does not appear in the facts. A rejected answer gets one repair attempt, then
   the next model, then rules-based advice labelled "Standard advice (not AI-generated)".

## How the solution works

1. **Pick a household.** Choose one of three samples, or describe your own: up to eight
   people with age group and conditions, routines, commutes and the home. Then search for a
   place (older names such as Bangalore or Gurgaon work) or use your location. Nothing is
   stored on a server: the household lives in a signed, HttpOnly cookie.
2. **Measured air.** The app finds the nearest CPCB stations from a stored list of 571. It
   asks the nearest first, and the next two only if needed. It works out the official AQI
   (the highest sub-index, valid only with at least three pollutants including PM2.5 or PM10).
3. **Timing.** The Open-Meteo (CAMS) hourly forecast for the next 24 hours finds the cleanest
   and worst 3-hour windows between 6 am and 10 pm.
4. **Facts and decisions.** Code builds the facts bundle and the rules for routines, windows
   and swaps.
5. **The plan.** The AI chain (Groq `openai/gpt-oss-120b`, then Gemini 3.5 Flash-Lite, then
   Gemini 3.1 Flash-Lite) writes the plan. The page draws it as road signs, with the next step
   largest and the figure where a road sign shows the distance. "How this was generated"
   shows the model, prompt version, time taken, every attempt, the facts sent and the raw reply.
6. **Ask.** The Ask box answers questions such as "Can the kids play at 5 pm?" from the same
   facts, under the same number guard, and declines off-topic requests.
7. **This week.** Tick "I did this" on today's commute swap or a routine moved indoors. Code
   works out that day's CO₂ avoided and the change in PM2.5 breathed, from that day's
   measured air, and the panel adds up the last seven days. The log lives in the same signed
   cookie.
8. **The sky.** The page's colour follows the time of day at the place (morning, afternoon,
   evening, dusk, night), from sunrise and sunset computed in code. It is dulled by the
   measured AQI band. Contrast stays WCAG AA in all 30 combinations, and a test checks them.

Identical AI requests are answered from a one-hour cache, station readings are cached for
15 minutes and the forecast for an hour, so repeat visits are fast and stay within the free
model quotas.

## Assumptions

- CPCB's `avg_value` in the data.gov.in feed is each pollutant's **sub-index** on the AQI
  scale, not a concentration. PM2.5 concentration is worked back from CPCB's breakpoints.
- Indoor PM2.5 is a steady-state estimate from outdoor air only, with published typical values
  for leakage, settling and air exchange. Cooking, incense and smoking make real rooms worse.
- Commute CO₂ factors come from the India GHG Program (2015). Exposure on the way, speeds and
  breathing rates come from a Delhi on-road study (Goel et al., 2015) and are applied to all
  cities. Metro CO₂ is from the Delhi Metro (61 g per passenger-km).
- The forecast is a regional model (about 45 km). Its values are never shown as the air
  quality, only used to rank hours.
- "Equal to N cigarettes" uses Berkeley Earth's 22 µg/m³ of PM2.5 for a day ≈ one cigarette.

Every value, with its source and caveats: [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md).

## Sample inputs for evaluators

On the start page, choose a sample, or set up your own household:

| Sample | What it shows |
|---|---|
| **Delhi family** (ITO, New Delhi) | A child's outdoor play and a grandmother's walk with asthma moved indoors on Poor or worse air. A car commute with a metro option. Purifier and incense. |
| **Bengaluru cyclist** (Koramangala) | A single adult whose cycle commute has no CO₂ to swap; on cleaner days the routines stay as they are |
| **Mumbai commuter** (Andheri East) | A father with a heart condition: offered the carpool, not the bus, because the bus adds polluted air on the way. A daughter's school run. |

Try your own: "Lucknow", "Salt Lake", "Gurgaon" or "Nirmal" (whose nearest station is about
110 km away, so the page says the local air may differ). In Ask, try "Can Aarav play cricket
at 5 pm?", or an off-topic request such as "Write me a poem" to see it declined. "योजना हिंदी
में" at the bottom of the page asks for the plan in Hindi.

## Data sources

- **Central Pollution Control Board**, real-time air quality, via
  [data.gov.in](https://www.data.gov.in/resource/real-time-air-quality-index-various-locations)
  (Government Open Data License, India).
- **[Open-Meteo](https://open-meteo.com/)**: air-quality forecast (CAMS, CC BY 4.0) and
  place search.
- Published sources for every constant are listed in [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md).

## Limitations

- No accounts or cross-device sync; the household lives in one browser's cookie. The cookie
  is signed (it cannot be altered) but not encrypted: whoever holds the browser can decode it.
- No indoor sensors: indoor values are estimates from outdoor air.
- Tailpipe PM2.5 per trip is not estimated (no current Indian per-kilometre data for today's
  vehicles).
- The number guard proves every number (and number words such as "twice" or "half") came from
  the facts, not that the AI used it in the right place. Each sign shows the facts it cites
  so a reader can check.
- Not medical advice: the app says when to keep medicines handy or see a doctor, nothing more.
- Free model quotas are limited. When every model is busy, the page shows labelled standard
  advice instead.

## Run it locally

```bash
uv sync
cp .env.example .env      # add DATA_GOV_API_KEY, GROQ_API_KEY, GEMINI_API_KEY
uv run uvicorn app.index:app --reload
```

## Quality checks

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy app tests scripts                  # strict
uv run pytest -W error --cov=app               # 289 tests, 95% branch-coverage gate (100% now)
uv run pytest -W error -m e2e                  # 31 browser tests: axe (WCAG 2.2 AA), widths, keyboard
```

CI runs the same checks plus a secret scan, a dependency audit and a repository-size budget
on every push. The tests never call a real service: CPCB, Open-Meteo and the AI models are
mocked with recorded replies.

## Project layout

| Path | What it holds |
|---|---|
| `app/air/` | CPCB, forecast and place-search clients; nearest-station lookup |
| `app/domain/` | Pure calculations: AQI, household, commute, indoor air, timing, sky, decision rules |
| `app/advice/` | The facts bundle, the plan and Ask tasks, and the standard advice |
| `app/ai/` | Model providers, the fallback chain and the number guard |
| `app/web/` | Routes, session, templates; `public/static/` holds CSS, fonts and htmx |
