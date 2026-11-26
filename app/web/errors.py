"""Errors as pages people can read, instead of the framework's JSON.

A request from htmx gets a short fragment that drops into the page; anything else gets a full
page with a way back. Messages never echo what was sent.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.advice.ask import QUESTION_MAX_CHARS, QUESTION_MIN_CHARS
from app.web.templating import templates

TITLES = {
    403: "That form has expired",
    404: "Page not found",
    405: "Page not found",
    422: "Some of that could not be read",
}


ASK_LENGTH = f"Please ask in {QUESTION_MIN_CHARS} to {QUESTION_MAX_CHARS} characters."
# The form field whose errors get their own message (the Ask box's question).
QUESTION_FIELD = "question"


def register_error_handlers(app: FastAPI) -> None:
    """Show HTTP and validation errors as readable pages.

    Args:
        app: The application.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, error: StarletteHTTPException) -> Response:
        # Only the CSRF refusal's reason is shown; other details stay out of the page.
        forbidden = error.status_code == status.HTTP_403_FORBIDDEN
        message = error.detail if forbidden and isinstance(error.detail, str) else None
        return _render(request, error.status_code, message)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, error: RequestValidationError) -> Response:
        about_question = any(QUESTION_FIELD in problem["loc"] for problem in error.errors())
        message = ASK_LENGTH if about_question else None
        return _render(request, status.HTTP_422_UNPROCESSABLE_CONTENT, message)


def _render(request: Request, code: int, message: str | None) -> Response:
    title = TITLES.get(code, "Something went wrong")
    context = {"code": code, "title": title, "message": message}
    name = "partials/error.html" if request.headers.get("hx-request") else "error.html"
    return templates.TemplateResponse(request, name, context, status_code=code)
