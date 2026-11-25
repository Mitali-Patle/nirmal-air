"""Ticking a step as done for the "This week" log (an htmx fragment)."""

from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, Response

from app.advice.week_steps import step_options
from app.domain.week import LogEntry, add_entry
from app.web.csrf import CsrfChecked
from app.web.routes.today import current_day
from app.web.session import load_log, save_log
from app.web.templating import templates
from app.web.week_view import week_view

router = APIRouter()


@router.post("/log", response_class=HTMLResponse, dependencies=[CsrfChecked])
async def log_step(request: Request, step: Annotated[str, Form(max_length=20)]) -> Response:
    """Record that a step was done today, with its impact worked out from today's air.

    Args:
        request: The incoming request.
        step: The step's id, such as "swap-1" or "indoors-2".

    Returns:
        The updated "This week" section.

    Raises:
        HTTPException: 404 when the step is not one of today's steps.
    """
    found = await current_day(request)
    if found is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    today = found[1].today
    options = step_options(today)
    option = next((item for item in options if item.id == step), None)
    if option is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "That step is not on today's plan.")
    day = today.now.date()
    entries = add_entry(load_log(request), LogEntry(day, option.id, option.label, option.impact))
    save_log(request, entries)
    context = {"week": week_view(entries, options, day), "announce": f"Logged: {option.label}."}
    return templates.TemplateResponse(request, "partials/week_logged.html", context)
