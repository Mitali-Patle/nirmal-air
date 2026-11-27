# Assumptions and sources

NirmalAir shows two kinds of numbers. **Measured** values come straight from CPCB stations.
**Estimates** are worked out in code from those measurements and the published values below.
Every estimate is labelled as one on screen. The constants live in
[`app/domain/assumptions.py`](../app/domain/assumptions.py); this page explains them.

## Air quality

| What | Value or rule | Source |
|---|---|---|
| AQI bands and health statements | Good 0–50 … Severe 401–500 | CPCB, National Air Quality Index (2014) |
| Station AQI | Highest pollutant sub-index; needs at least 3 pollutants, one of them PM2.5 or PM10 | CPCB NAQI |
| CPCB `avg_value` | Read as each pollutant's **sub-index**, not its concentration | Checked against OpenAQ's concentration for the same station (Talkatora, Delhi: sub-index 324 while OpenAQ reported 94 µg/m³) |
| PM2.5 concentration | Worked back from the PM2.5 sub-index with CPCB's breakpoints; above 400 it is taken as 250 µg/m³, the Severe band's floor, so it is an underestimate | CPCB NAQI breakpoint table |
| Freshness | Readings older than 3 hours are not used | Our choice: CPCB updates hourly |
| Forecast | Open-Meteo (CAMS model, about 45 km grid) is only used to **rank hours** | Its absolute values were far from measured ones (Delhi, 23 Nov: 48 vs 94 µg/m³) |

## Cleanest and worst times

The forecast's next 24 hours are cut into 3-hour windows between 6 am and 10 pm. The window
with the lowest average PM2.5 is the cleanest; the highest is the worst. Hours more than 15%
below or above the day's median are marked "cleaner" or "dirtier" in the hourly strip.

## Indoor air

Steady-state mass balance for outdoor particles coming indoors:

`indoor = P × a × outdoor / (a + k + CADR / V)`

| Symbol | Meaning | Value used |
|---|---|---|
| P | Share of fine particles that get in | 0.8 with windows shut, 1.0 with windows open |
| a | Outdoor air changes per hour | 1.0 shut (a typical Indian home, not airtight), 5.0 open |
| k | Particles settling indoors, per hour | 0.2 |
| CADR | Purifier clean-air delivery rate | From the household (m³/h, printed on the box) |
| V | Room volume | Floor area × 3 m ceiling |

For a home without a purifier, the page also shows what a typical one would do, taking a
common mid-range rating of 250 m³/h (an assumption, not a product recommendation).

The model is the one reviewed by Chen and Zhao, *Atmospheric Environment* 45 (2011); the
values are assumptions from the middle of published ranges, not measurements of any home.
It leaves out indoor sources: cooking, incense, mosquito coils and smoking make a room worse
than estimated. The purifier figure assumes the room stays shut and the purifier runs at the
CADR given, so real rooms usually do somewhat less well.

## Houseplants

Potted plants are not offered as a fix. A review of 196 sealed-chamber tests found a median
clean air delivery rate of 0.023 m³ an hour per plant; matching a building's own air
exchange would take 10 to 1,000 plants per m² of floor (Cummings and Waring, *Journal of
Exposure Science & Environmental Epidemiology* 30, 2020). The tests measured indoor chemicals
(VOCs); for PM2.5, leaves catch only a little. The page says so in "At home".

## Cigarette equivalent

Breathing 22 µg/m³ of PM2.5 for 24 hours does about the same harm as smoking one cigarette
(Berkeley Earth, Muller and Muller, *Air Pollution and Cigarette Equivalence*, 2015). It is a
way to picture harm, not a medical measure.

## Commutes

| Mode | Speed (km/h) | PM2.5 on the way vs outdoors | Breathing (L/min) | CO₂ (kg/km) |
|---|---|---|---|---|
| Walk | 4 | 1.4× | 15 | 0 |
| Cycle | 17 | 1.1× | 35 | 0 |
| Scooter or motorbike | 24 | 1.3× | 10 | 0.0368 per vehicle |
| Auto-rickshaw (CNG) | 22 | 1.3× | 10 | 0.10768 per vehicle |
| Bus | 14 | 1.2× | 10 | 0.015161 per passenger |
| Metro | 32 | 0.8× | 10 | 0.061 per passenger |
| Car (petrol hatchback, AC on recirculation) | 20 | 0.5× | 10 | 0.140 per vehicle |
| SUV (diesel) | 20 | 0.5× | 10 | 0.210 per vehicle |

- **Speed, exposure and breathing**: Goel et al., *On-road PM2.5 pollution exposure in
  multiple transport microenvironments in Delhi*, Atmospheric Environment 123 (2015),
  abstract and Table 3. Measured in Delhi's morning rush; used for all Indian cities.
- **Bus and metro trips** add 10 minutes of walking and 5 of waiting (bus stop 1.2×,
  underground metro station 1.3× outdoors), as in the same study.
- **Road CO₂**: India GHG Program, *India Specific Road Transport Emission Factors* (2015),
  values that include its uplift for real-world driving.
- **Metro CO₂**: Goel and Tiwari, *Case Study of Metro Rails in Indian Cities*, UNEP DTU
  Partnership (2014): 61 g per passenger-km for the Delhi Metro, from its electricity use.
- Per-vehicle CO₂ is split between the people sharing it (carpools). A carpool swap assumes
  three people.
- Walking is offered for trips up to 2 km and cycling up to 8 km. The metro is offered only
  when the household says it is an option for that trip.

**What a swap can show:** a car with AC on recirculation keeps out more PM2.5 than a bus or a
walk to the metro, so a lower-CO₂ swap can mean breathing more polluted air on the way. The app
shows both numbers rather than hiding the trade-off.

**Not estimated:** tailpipe PM2.5 per trip. The only Indian per-kilometre measurements we found
(ARAI, 2008) are for vehicles much older than today's BS-VI fleet, and road dust, which they
leave out, is a large part of traffic PM2.5.

## This week

- A logged commute swap counts both directions of one day: CO₂ avoided is the difference
  between the usual trip and the swap, and the change in PM2.5 breathed uses that day's
  outdoor PM2.5 and the exposure ratios and breathing rates above.
- A routine moved indoors counts the air breathed during it: its minutes × the breathing rate
  for the activity (15 L/min walking, errands or the school run; 35 L/min for play or sport,
  US EPA values as used by Goel et al. 2015). This is multiplied by the difference between
  outdoor PM2.5 and the estimated indoor level with windows shut.
- Each step is worked out on the day it is ticked and stored with its numbers, so a week's
  totals do not change when today's air does.
