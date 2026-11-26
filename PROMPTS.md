# Prompts and how they evolved

How NirmalAir was built with AI, and how its own prompts changed after live testing.

## Tools and why

| Tool | Used for | Why |
|---|---|---|
| Claude Code (Claude Opus) | Planning, code, tests, docs, live checks | One agent across spec, build and verification |
| Impeccable (design skill) | Product brief, a dice-rolled visual direction, a decision page, an independent finish review, DESIGN.md | To avoid the generic "AI-made" look: the direction came from Indian road signs, not a template |
| Groq `openai/gpt-oss-120b` | The app's plan and answers | Fastest in testing: a full plan in 2 to 3 s |
| Gemini 3.5 and 3.1 Flash-Lite | Backups in the chain | Separate quotas when Groq's 8,000 tokens a minute run out |

## The app's prompt flow

1. Code builds the **facts bundle**: one sentence per fact, each with an id and a kind
   (measured, forecast, estimate, CPCB guidance, your household).
2. The **plan prompt** (`app/advice/plan.py`, version `plan-v5`) asks for strict JSON: 4 to 8
   items (up to 12 for a large household), each with a slot, a member, an action under 12
   words, a reason under 16 words and the fact ids it cites.
3. Code checks every item:
   - every number appears in the facts;
   - the fact ids are real;
   - the member exists;
   - every sensitive member, routine and commute is covered.

   A failed answer goes back once with the problems listed, then to the next model, then to
   standard advice.
4. The **ask prompt** (`app/advice/ask.py`) answers one question from the same facts. It may
   answer, ask for clarification, or decline off-topic requests. The question is sent as data.

## What changed after live tests

| Seen in a live run | Change |
|---|---|
| The model picked "2 pm" inside the cleanest window and added "10 minutes" | The guard caught both. Prompt rule: quote times as the fact gives them, add no durations |
| It left out the child's play and the grandmother's walk | The check now requires an item for every sensitive member, routine and commute |
| It moved an asthmatic grandmother's walk to the cleanest hours on Very Poor air | **Code now decides** each routine from CPCB's bands (`app/domain/guidance.py`); the AI explains |
| It said to shut windows *during* the cleanest window | **Code now decides** the windows rule; the AI quotes it |
| It wrote "share with 2 others" when the fact said 3 people | The fact now says "Asha and 2 others", so the natural phrasing is a real number |
| It suggested the bus to a father with a heart condition (371% more polluted air on the way) | **Code now ranks** swaps: sensitive people get swaps that do not add exposure first |
| A headline said the bus would "limit exposure" | `plan-v2`: never call a swap healthier when its fact says more polluted air. It slipped into the headline again, so `plan-v4` dropped the headline: it only repeated the signs |
| An 8-person joint family always failed the 8-item limit | `plan-v3`: up to 12 items for a large household |
| The page was a lot of reading | `plan-v4`: actions under 12 words, reasons under 16 |
| `gpt-oss-20b` passed the guard but said a car emits less CO₂ than a bus | Not added as a backup model |
| Asked for Hindi, `gpt-oss-120b` sometimes answered in English | `plan-v5` / `ask-v2`: the rule names Devanagari, and **code now checks** it: a Hindi answer with no Devanagari goes back for repair, then to the next model |

The pattern: each time the AI made a judgement call wrong, the judgement moved into tested
code, and the AI was left to explain it.

## AI and me

- **Decided by me:**
  - the data sources (CPCB first, the forecast only for timing, OpenAQ held in reserve);
  - no database;
  - the name;
  - the look: first a road-sign direction from the dice-rolled options, then, after seeing it
    on my phone, a calmer "paper and ink" redesign from my own reference images and my choice
    of heading font;
  - the idea that the page colour follows the time of day and is dulled by the measured AQI;
  - every approval before code.
- **Done by AI under review:**
  - research into published sources, read from the PDFs themselves;
  - code and tests;
  - live checks against CPCB and the models;
  - an independent design review, whose eight fixes were all applied.
