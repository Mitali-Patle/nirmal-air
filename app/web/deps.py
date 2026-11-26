"""What the routes share: the app's services, today's data for the saved household, the AI.

The services live on `app.state` as one typed object, so a route gets them through
`AppServices` (a FastAPI dependency) instead of reading untyped attributes.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

import httpx
from fastapi import Depends, Request
from pydantic import BaseModel

from app.ai.chain import AIChain
from app.ai.task import AIResult, AITask
from app.air.lookup import AirLookup
from app.air.places import PlaceFinder
from app.config import Settings
from app.services.today import Day, PlaceChoice, TodayService
from app.web.limits import AILimits
from app.web.session import load_household


@dataclass
class Services:
    """The long-lived objects the routes use, made once at start-up.

    Not frozen: tests swap in a fixed clock and a scripted AI chain.
    """

    settings: Settings
    http: httpx.AsyncClient
    air_lookup: AirLookup | None
    today: TodayService
    places: PlaceFinder
    ai: AIChain
    ai_limits: AILimits
    clock: Callable[[], datetime]


def get_services(request: Request) -> Services:
    """The app's services.

    Args:
        request: The incoming request.

    Returns:
        The services made at start-up.
    """
    found: Services = request.app.state.services
    return found


AppServices = Annotated[Services, Depends(get_services)]


@dataclass(frozen=True)
class SavedDay:
    """The saved household's place and today's data for it."""

    place: PlaceChoice
    day: Day


async def saved_day(request: Request, *, weather: bool = False) -> SavedDay | None:
    """Today's data for the household saved in the session.

    Args:
        request: The incoming request.
        weather: Also fetch the weather (only the Today page draws the sky).

    Returns:
        The place and the day, or None when no household is saved.
    """
    saved = load_household(request)
    if saved is None:
        return None
    place, household = saved
    app = get_services(request)
    return SavedDay(place, await app.today.day(place, household, app.clock(), weather=weather))


async def ask_ai[C, T: BaseModel](request: Request, task: AITask[C, T], context: C) -> AIResult[T]:
    """Run an AI task under the visitor's and the instance's rate limits.

    Args:
        request: The incoming request, whose client the limits count.
        task: What to ask.
        context: The facts the answer must rest on.

    Returns:
        The checked answer, or the task's standard advice.
    """
    app = get_services(request)
    return await app.ai.run(task, context, allow=lambda: app.ai_limits.allow(request))
