# Contributing

## Set up

```bash
uv sync
uv run pre-commit install   # ruff, mypy, Biome, gitleaks and file rules on every commit
cp .env.example .env        # optional: DATA_GOV_API_KEY, GROQ_API_KEY, GEMINI_API_KEY
uv run uvicorn app.index:app --reload
```

## Checks (the same ones CI runs)

```bash
uv run pre-commit run --all-files    # lint, format, types, secrets, JS and CSS
uv run pytest -W error --cov=app     # unit tests and doctests, 95% branch-coverage gate
uv run pytest -W error -m e2e        # browser tests: journeys, axe (WCAG 2.2 AA), keyboard
```

## Conventions

- **AI explains, code calculates, real data decides.** A new number is computed in
  `app/domain/` (pure functions, no I/O) and reaches the model as a fact in `app/advice/`, with
  its source in `docs/ASSUMPTIONS.md`. The model never computes or decides.
- **Adding a fact:** give it an id in `app/advice/facts.py`, build it in the matching
  `*_facts.py` module, and add a test that checks its sentence and figure.
- **Changing a prompt:** bump its version (`PLAN_VERSION` or `ASK_VERSION`) and add a row to
  `PROMPTS.md` saying what changed and why.
- **Names and messages:** user-facing text is plain English, and errors say what to do next.
- **Front end:** server-rendered Jinja with htmx; scripts are small ES modules in
  `public/static/js/`; colours are custom properties set per sky phase (`tokens.css`, and
  `sky.css` for the decorative sky band), and new text colours are added to
  `tests/test_contrast.py`.
- **Security:** see the checklist at the end of `SECURITY.md`.

## Commits

Work happens on `main` only (a hook enforces it; the repository keeps exactly one branch).
Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`).
