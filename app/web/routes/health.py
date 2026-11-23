"""Health endpoints: `/healthz` says the process is up, `/readyz` that CPCB data flows."""

from datetime import datetime

from fastapi import APIRouter, Request, Response, status

from app.air.cpcb import IST
from app.air.lookup import AirLookup

router = APIRouter(tags=["health"])
# Central Delhi has several stations, so a lookup there fails only if the feed is down.
PROBE_POINT = (28.6139, 77.2090)


@router.get("/healthz")
def healthz() -> dict[str, str]:
    """Report that the process is up, without calling any outside service.

    Returns:
        A fixed status payload.
    """
    return {"status": "ok"}


@router.head("/healthz", include_in_schema=False)
def healthz_head() -> Response:
    """Answer uptime monitors that check with HEAD.

    Returns:
        An empty 200 response.
    """
    return Response()


@router.get("/readyz")
async def readyz(request: Request, response: Response) -> dict[str, str]:
    """Report whether a live CPCB reading can be fetched from where the app runs.

    The reply never says why the data is unavailable, so no configuration is exposed.

    Args:
        request: The incoming request, for the app's air lookup.
        response: Response used to set the status code.

    Returns:
        `{"status": "ok"}` with 200, or `{"status": "unavailable"}` with 503.
    """
    lookup: AirLookup | None = request.app.state.air_lookup
    if lookup is None or await lookup.measured_air(*PROBE_POINT, datetime.now(IST)) is None:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable"}
    return {"status": "ok"}
