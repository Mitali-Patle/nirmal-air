"""The Today page, its plan (loaded by htmx so the air shows at once) and the Ask box."""

import json
from typing import Annotated, Any

from fastapi import APIRouter, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.advice.ask import AskContext, Question
from app.advice.bundle import build_facts
from app.advice.facts import FAR_STATION_KM
from app.advice.plan import Language, PlanContext
from app.advice.tasks import ASK_TASK, PLAN_TASK
from app.advice.week_steps import step_options
from app.domain.sky import MAX_HAZE, haze_level
from app.services.today import Day, PlaceChoice
from app.web.csrf import CsrfChecked
from app.web.deps import AppServices, ask_ai, saved_day
from app.web.session import (
    THEME_LABELS,
    ThemeChoice,
    load_household,
    load_log,
    sample_title,
    save_theme,
    theme_choice,
)
from app.web.sky_view import scene_for, sky_for
from app.web.templating import templates
from app.web.views import plan_board, strip
from app.web.week_view import week_view

router = APIRouter()
Lang = Annotated[str, Query(pattern="^(en|hi)$")]


@router.get("/today", response_class=HTMLResponse)
async def today(request: Request, lang: Lang = "en") -> Response:
    """The household's day: measured air, timing and estimates now; the plan follows.

    Args:
        request: The incoming request.
        lang: Language of the AI's text, "en" or "hi".

    Returns:
        The page, or a redirect to the start page when no household is saved.
    """
    saved = await saved_day(request, weather=True)
    if saved is None:
        return RedirectResponse("/", status.HTTP_303_SEE_OTHER)
    context = _context(request, saved.place, saved.day, lang)
    return templates.TemplateResponse(request, "today.html", context)


@router.get("/today/plan", response_class=HTMLResponse)
async def plan(request: Request, lang: Lang = "en") -> Response:
    """Today's plan as steps on the day's rail, with how it was generated (an htmx fragment).

    Args:
        request: The incoming request.
        lang: Language of the AI's text.

    Returns:
        The plan fragment, or an empty response when no household is saved.
    """
    saved = await saved_day(request)
    if saved is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    plan_context = _plan_context(saved.day, lang)
    result = await ask_ai(request, PLAN_TASK, plan_context)
    context = {
        "board": plan_board(result.value, plan_context.facts, saved.day.today.now),
        "provenance": result.provenance,
        "lang": lang,
    }
    return templates.TemplateResponse(request, "partials/plan.html", context)


@router.post("/ask", response_class=HTMLResponse, dependencies=[CsrfChecked])
async def ask(
    request: Request,
    question: Annotated[Question, Form()],
    lang: Annotated[str, Form(pattern="^(en|hi)$")] = "en",
) -> Response:
    """Answer a question about today from the facts (an htmx fragment).

    Args:
        request: The incoming request.
        question: The visitor's question (its length limits are on `Question`).
        lang: Language of the answer.

    Returns:
        The answer fragment.
    """
    saved = await saved_day(request)
    if saved is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    plan_context = _plan_context(saved.day, lang)
    result = await ask_ai(request, ASK_TASK, AskContext(question, plan_context))
    by_id = {fact.id: fact for fact in plan_context.facts}
    page = {
        "question": question,
        "answer": result.value,
        "cited": [by_id[fact_id] for fact_id in result.value.fact_ids if fact_id in by_id],
        "provenance": result.provenance,
        "lang": lang,
    }
    return templates.TemplateResponse(request, "partials/answer.html", page)


def _plan_context(day: Day, lang: str) -> PlanContext:
    """The day's facts in the visitor's language, as the AI tasks take them."""
    language = Language.HINDI if lang == "hi" else Language.ENGLISH
    return PlanContext(day.today, build_facts(day.today), language)


@router.post("/theme", dependencies=[CsrfChecked])
async def set_theme(
    request: Request,
    services: AppServices,
    theme: Annotated[ThemeChoice, Form()],
    lang: Annotated[str, Form(pattern="^(en|hi)$")] = "en",
    haze: Annotated[int, Form(ge=0, le=MAX_HAZE)] = 0,
) -> Response:
    """Remember the visitor's colours, and repaint the page without reloading it.

    With htmx the reply is the new sky band, its note and the colour form, and an HX-Trigger
    event carries the phase, haze and theme for theme.js to set on the page. Only the cached
    weather is needed: the page sends its own haze level, so no air data is fetched again.
    Without JavaScript the form posts normally and Today reloads in the same language.

    Args:
        request: The incoming request.
        services: The app's services, for the clock and the weather.
        theme: Dark, follow the sky, or light.
        lang: The plan's language, kept across a reload.
        haze: The page's haze level from the measured AQI band (decoration only).

    Returns:
        The sky fragment, or a redirect back to Today.
    """
    save_theme(request, theme)
    back = RedirectResponse(
        "/today?lang=hi" if lang == "hi" else "/today", status.HTTP_303_SEE_OTHER
    )
    saved = load_household(request)
    if not request.headers.get("hx-request") or saved is None:
        return back
    place, now = saved[0], services.clock()
    sky = sky_for(place, now, haze, theme)
    scene = scene_for(place, now, sky, await services.today.weather(place))
    context = {"sky": sky, "scene": scene, "theme_labels": THEME_LABELS, "lang": lang}
    response = templates.TemplateResponse(request, "partials/theme.html", context)
    change = {"phase": sky.phase.value, "haze": sky.haze, "theme": sky.theme.value}
    response.headers["HX-Trigger"] = json.dumps({"theme-change": change})
    return response


def _context(request: Request, place: PlaceChoice, day: Day, lang: str) -> dict[str, Any]:
    today = day.today
    air = today.air
    facts = {fact.id: fact for fact in build_facts(today)}
    haze = haze_level(air.aqi.category if air else None)
    sky = sky_for(place, today.now, haze, theme_choice(request))
    return {
        "air": air,
        "sky": sky,
        "scene": scene_for(place, today.now, sky, day.weather),
        "theme_labels": THEME_LABELS,
        "today": today,
        "far": air is not None and air.nearby.distance_km > FAR_STATION_KM,
        "facts": facts,
        "strip": strip(day.hours, today.timing),
        "lang": lang,
        "sample": sample_title(request),
        "week": week_view(load_log(request), step_options(today), today.now.date()),
    }
