"""The Today page, its plan (loaded by htmx so the air shows at once) and the Ask box."""

from typing import Annotated, Any

from fastapi import APIRouter, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.advice.ask import AskContext, Question
from app.advice.bundle import build_facts
from app.advice.facts import FAR_STATION_KM
from app.advice.plan import Language, PlanContext
from app.advice.tasks import ASK_TASK, PLAN_TASK
from app.advice.week_steps import step_options
from app.ai.chain import AIChain
from app.services.today import Day, PlaceChoice, TodayService
from app.web.limits import AILimits
from app.web.session import CsrfChecked, load_household, load_log, sample_title, theme_choice
from app.web.templating import templates
from app.web.views import KIND_LABELS, scene_for, sign_board, sky_for, strip, week_view

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
    found = await current_day(request, weather=True)
    if found is None:
        return RedirectResponse("/", status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "today.html", _context(request, *found, lang))


@router.get("/today/plan", response_class=HTMLResponse)
async def plan(request: Request, lang: Lang = "en") -> Response:
    """Today's plan as signs, with how it was generated (an htmx fragment).

    Args:
        request: The incoming request.
        lang: Language of the AI's text.

    Returns:
        The plan fragment, or an empty response when no household is saved.
    """
    found = await current_day(request)
    if found is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    day = found[1]
    facts = build_facts(day.today)
    chain: AIChain = request.app.state.ai
    limits: AILimits = request.app.state.ai_limits
    plan_context = PlanContext(day.today, facts, _language(lang))
    result = await chain.run(PLAN_TASK, plan_context, allow=lambda: limits.allow(request))
    context = {
        "board": sign_board(result.value, facts, day.today.now),
        "provenance": result.provenance,
        "kind_labels": KIND_LABELS,
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
        question: The visitor's question, 3 to 200 characters.
        lang: Language of the answer.

    Returns:
        The answer fragment.
    """
    found = await current_day(request)
    if found is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    day = found[1]
    facts = build_facts(day.today)
    context = AskContext(question, PlanContext(day.today, facts, _language(lang)))
    chain: AIChain = request.app.state.ai
    limits: AILimits = request.app.state.ai_limits
    result = await chain.run(ASK_TASK, context, allow=lambda: limits.allow(request))
    by_id = {fact.id: fact for fact in facts}
    page = {
        "question": question,
        "answer": result.value,
        "cited": [by_id[fact_id] for fact_id in result.value.fact_ids if fact_id in by_id],
        "provenance": result.provenance,
        "kind_labels": KIND_LABELS,
        "lang": lang,
    }
    return templates.TemplateResponse(request, "partials/answer.html", page)


async def current_day(request: Request, *, weather: bool = False) -> tuple[PlaceChoice, Day] | None:
    """The saved household's place and today's data for it.

    Args:
        request: The incoming request.
        weather: Also fetch the weather (only the Today page draws the sky).

    Returns:
        The place and the day, or None when no household is saved.
    """
    saved = load_household(request)
    if saved is None:
        return None
    service: TodayService = request.app.state.today
    return saved[0], await service.day(*saved, request.app.state.clock(), weather=weather)


def _language(lang: str) -> Language:
    return Language.HINDI if lang == "hi" else Language.ENGLISH


def _context(request: Request, place: PlaceChoice, day: Day, lang: str) -> dict[str, Any]:
    today = day.today
    air = today.air
    facts = {fact.id: fact for fact in build_facts(today)}
    sky = sky_for(place, today.now, air.aqi.category if air else None, theme_choice(request))
    return {
        "today": today,
        "air": air,
        "far": air is not None and air.nearby.distance_km > FAR_STATION_KM,
        "facts": facts,
        "strip": strip(day.hours, today.timing),
        "sky": sky,
        "scene": scene_for(place, today.now, sky, day.weather),
        "lang": lang,
        "sample": sample_title(request),
        "week": week_view(load_log(request), step_options(today), today.now.date()),
    }
