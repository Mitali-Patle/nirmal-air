"""Errors as pages people can read, instead of the framework's JSON.

A request from htmx gets a short fragment that drops into the page; anything else gets a full
page with a way back. Messages never echo what was sent.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.web.templating import templates

TITLES = {
    403: "That form has expired",
    404: "Page not found",
    405: "Page not found",
    422: "Some of that could not be read",
}


def register_error_handlers(app: FastAPI) -> None:
    """Show HTTP and validation errors as readable pages.

    Args:
        app: The application.
    """

    async def http_error(request: Request, error: Exception) -> Response:
        code = error.status_code if isinstance(error, StarletteHTTPException) else 500
        detail = error.detail if isinstance(error, StarletteHTTPException) else None
        message = detail if isinstance(detail, str) and code == 403 else None  # noqa: PLR2004
        return _render(request, code, message)

    async def invalid_request(request: Request, error: Exception) -> Response:
        return _render(request, 422, None)

    app.add_exception_handler(StarletteHTTPException, http_error)
    app.add_exception_handler(RequestValidationError, invalid_request)


def _render(request: Request, code: int, message: str | None) -> Response:
    title = TITLES.get(code, "Something went wrong")
    context = {"code": code, "title": title, "message": message}
    name = "partials/error.html" if request.headers.get("hx-request") else "error.html"
    return templates.TemplateResponse(request, name, context, status_code=code)
