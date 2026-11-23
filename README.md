# NirmalAir

A GenAI clean-air assistant for Indian families living through winter smog. It reads the
**measured** air at the nearest CPCB station, then gives each household a plan for the day,
indoor steps and lower-emission choices, with the impact of each choice worked out in code.

> Work in progress for PromptWars Virtual, Challenge 6 (deadline 29 Nov 2026). This README
> grows with the app.

## Chosen vertical

Urban Air Quality Assistant.

## Approach and logic

**AI explains, code calculates, real data decides.** Air quality comes only from CPCB's
real-time feed (via data.gov.in); every number on screen is computed by tested code; the AI
turns those numbers into advice for one household and says why.

## How the solution works

1. You search any Indian city or locality (older names such as Bangalore or Gurgaon work).
2. The app finds the nearest CPCB station with a valid, recent reading and works out the
   official AQI from its pollutant sub-indices (CPCB's rule: at least three pollutants,
   including PM2.5 or PM10). Station, distance, source and time are always shown.
3. An hourly forecast (Open-Meteo) is used only to rank hours: the cleanest and worst times.

Coming next: the household profile, the AI plan, indoor estimates and commute swaps.

## Assumptions

- CPCB's `avg_value` is each pollutant's sub-index on the national AQI scale.
- Readings older than three hours are not used.
- The forecast is a model estimate and is never shown as the measured value.

## Run it locally

```bash
uv sync
cp .env.example .env   # add your keys
uv run uvicorn app.index:app --reload
uv run pytest
```

## Data sources

- Central Pollution Control Board, real-time AQI, via [data.gov.in](https://www.data.gov.in/resource/real-time-air-quality-index-various-locations)
  (Government Open Data License – India).
- [Open-Meteo](https://open-meteo.com/) air quality forecast (CAMS, CC BY 4.0) and geocoding.
