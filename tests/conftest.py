import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import httpx
import pytest

FIXTURES = Path(__file__).with_name("fixtures")


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient() as http_client:
        yield http_client
