"""Liveness endpoint for uptime checks; it never calls an outside service."""

from fastapi import APIRouter, Response

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    """Report that the process is up.

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
