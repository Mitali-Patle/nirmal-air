# Security and privacy

NirmalAir has no accounts and no database. This page lists what it holds, where it sends it,
and the controls around each part, with the files that implement them.

## Reporting a problem

Please do not put the details in a public issue. Open an issue titled "Security contact"
with no details, and the maintainer will arrange a private channel. Then send the page or
request, what you expected and what happened.

## What the app holds

| Data | Where it lives | For how long |
|---|---|---|
| The household: first names, age group, sensitivities (lung, heart, pregnancy), routines, commutes and home | The visitor's own browser, in one signed cookie (`app/web/session.py`) | 30 days, or until "Forget this household" |
| The chosen place (its name and coordinates) | The same cookie | The same |
| "This week" log, colour choice, CSRF token | The same cookie | The same |
| Air readings, forecasts, place searches, AI answers | Server memory caches, per instance, keyed by place or by the whole request | 15 minutes to a day (`docs/ARCHITECTURE.md#efficiency`) |

Nothing is written to disk or a database, and the app logs nothing about visitors.

**Sent to others:** the place name goes to Open-Meteo's place search, coordinates to its
forecast, and the facts bundle (place, time, first names, age groups and sensitivities, and the
code-made facts) to the AI provider over HTTPS: Groq first, Google Gemini if Groq fails. No
account, address, IP address or exact location is sent to a model.

## Controls

| Area | Control | Where |
|---|---|---|
| Cookie | Signed (HMAC) so it cannot be altered; HttpOnly, SameSite=Lax, Secure in production; 30-day lifetime. Packed and size-tested to stay under 4 KB. Signed, not encrypted: whoever holds the browser can read it, so it holds no identifiers beyond first names, and "Forget this household" clears it. | `app/main.py`, `app/web/session.py`, `app/web/cookie.py` |
| Forms | A random CSRF token per session, compared in constant time, on every POST (htmx posts included). | `app/web/csrf.py` |
| Inputs | Every field validated with limits (Pydantic): names up to 20 letters, at most 8 people, 6 routines and 4 trips, numbers in range. The place always comes from the geocoder or a validated location, never from typed text. Request bodies over 16 KB are refused (413). | `app/domain/household.py`, `app/web/place_choice.py`, `app/web/security.py` |
| Prompt injection | Names and questions reach the model inside a JSON payload, and the prompts say they are data, not instructions. Decisions are made in code, not by the model. The answer cache is keyed by the whole request, so one visitor's text never reaches another. | `app/advice/plan.py`, `app/advice/ask.py` |
| AI output | Every number must appear in the facts (digits and number words, English and Hindi); fact ids and member names are checked; a failed answer is repaired once, then replaced by labelled standard advice. The answer is shown as escaped text (Jinja autoescape), never as HTML. | `app/ai/guard.py`, `app/advice/plan.py`, `app/web/templating.py` |
| Abuse and cost | Per-client rate limits: 60 requests a minute for pages and lookups, 20 AI calls in 10 minutes, and 60 AI calls a minute per instance. Over the limit: 429, or the labelled standard advice for the plan. The client address comes only from headers Vercel's proxy sets itself. | `app/web/limits.py`, `app/web/deps.py` |
| Browser | Content Security Policy with only the app's own origin and no inline code; frame denial; `nosniff`; strict referrer; permissions limited to geolocation on this site; same-origin opener and resource policies. In production, HSTS and `upgrade-insecure-requests`. | `app/web/security.py` |
| Errors | Readable error pages and htmx fragments that never echo what was sent; API docs are off in production. | `app/web/errors.py`, `app/main.py` |
| Secrets | API keys only in environment variables, held as `SecretStr`; production refuses to start without the data key or with a session secret under 32 characters. `.env` files are blocked from commits. | `app/config.py`, `.pre-commit-config.yaml` |
| Supply chain | Locked dependencies (`uv.lock`); pip-audit fails CI on a known vulnerability; CodeQL scans Python and JavaScript; gitleaks scans every commit and the whole history; GitHub Actions pinned to commit SHAs; htmx vendored byte-for-byte with its hash in `public/static/vendor/VENDOR.md`. | `.github/workflows/` |

## Residual risks, and why they are accepted

- **Rate limits are per serverless instance.** They stop a loop or a script, not a determined
  attacker spread over many instances. A shared store (Redis) would close this, at the cost of
  a network call on every request; the free model quotas are the real ceiling either way.
- **The cookie is readable by whoever holds the browser.** Encrypting it would protect the same
  data from the same person; on a shared device "Forget this household" is the control.
- **The model provider sees the facts bundle.** It holds first names and sensitivities, which
  the plan needs to address each person. Nothing more identifying is sent.

## Checklist for changes

- A new form field gets a limit in the Pydantic model and a test for the error.
- A new route that calls an outside service depends on the page or AI rate limit.
- A new AI task runs its answer through `FactGuard` and has a standard-advice fallback.
- New front-end code lives in `public/static/` (no inline script or style; the CSP forbids it).
