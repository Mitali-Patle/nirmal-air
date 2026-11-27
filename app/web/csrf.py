"""CSRF protection: a random token in the session, checked on every POST.

Every form, including the ones htmx posts, sends it as the hidden `csrf` field.
"""

import secrets
from typing import Annotated

from fastapi import Depends, Form, HTTPException, Request, status

CSRF_KEY = "csrf"


def csrf_token(request: Request) -> str:
    """This visitor's CSRF token, created on first use.

    Args:
        request: The incoming request.

    Returns:
        A random token kept in the session.
    """
    token = request.session.get(CSRF_KEY)
    if not isinstance(token, str):
        token = secrets.token_urlsafe(32)
        request.session[CSRF_KEY] = token
    return token


async def require_csrf(request: Request, csrf: Annotated[str | None, Form()] = None) -> None:
    """Reject a POST whose CSRF token (the form's hidden field) does not match the session.

    Args:
        request: The incoming request.
        csrf: The token sent in the form, if any.

    Raises:
        HTTPException: 403 when the token is missing or wrong.
    """
    sent = csrf or ""
    expected = request.session.get(CSRF_KEY)
    if not isinstance(expected, str) or not secrets.compare_digest(sent, expected):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "The form expired. Reload and try again.")


CsrfChecked = Depends(require_csrf)
