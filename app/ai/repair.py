"""The one repair attempt: telling a model why its answer was rejected and asking again."""

import json
from collections.abc import Sequence

from pydantic import ValidationError

from app.ai.task import OutputRejectedError

MAX_PROBLEMS = 5
MAX_REPLY_CHARS = 4000


def rejection_reasons(error: ValidationError | OutputRejectedError) -> list[str]:
    """Short, model-readable reasons an answer was rejected.

    Args:
        error: The schema validation error or the rule check's rejection.

    Returns:
        At most five reasons.
    """
    if isinstance(error, OutputRejectedError):
        return error.problems[:MAX_PROBLEMS]
    return [
        f"{'.'.join(str(part) for part in item['loc']) or 'answer'}: {item['msg']}"
        for item in error.errors()[:MAX_PROBLEMS]
    ]


def repair_request(user: str, previous: str, problems: Sequence[str]) -> str:
    """The original request plus the rejected answer and what to fix, for one more try.

    Args:
        user: The original request.
        previous: The model's rejected answer.
        problems: What was wrong with it.

    Returns:
        The new request text.
    """
    note = {
        "your_previous_answer": previous[:MAX_REPLY_CHARS],
        "fix_these_problems": list(problems),
    }
    return f"{user}\n\nYour previous answer was rejected. {json.dumps(note, ensure_ascii=False)}"
