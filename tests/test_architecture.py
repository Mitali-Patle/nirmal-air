"""The layers only depend inwards: pure calculations never import the code around them."""

import ast
import re
from pathlib import Path

import pytest

from app.advice.facts import FactId

APP = Path(__file__).resolve().parent.parent / "app"
# Each layer and the app packages it may import. `app.web` and `app.main` may use them all.
ALLOWED = {
    "domain": {"app.domain"},
    "ai": {"app.ai", "app.cache"},
    "air": {"app.air", "app.domain", "app.cache", "app.config"},
    "advice": {"app.advice", "app.domain", "app.air", "app.ai"},
    "services": {"app.services", "app.air", "app.domain", "app.advice", "app.cache"},
}


def app_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app."):
            names.add(node.module)
        elif isinstance(node, ast.Import):
            names |= {alias.name for alias in node.names if alias.name.startswith("app.")}
    return names


@pytest.mark.parametrize("layer", sorted(ALLOWED))
def test_each_layer_imports_only_what_it_may(layer: str) -> None:
    allowed = ALLOWED[layer]
    for path in (APP / layer).rglob("*.py"):
        for module in app_imports(path):
            assert any(module == ok or module.startswith(f"{ok}.") for ok in allowed), (
                f"{path.relative_to(APP)} imports {module}"
            )


def test_templates_name_only_facts_that_exist() -> None:
    names = set()
    for template in (APP / "web" / "templates").rglob("*.html"):
        names |= set(re.findall(r"\bfacts\.([a-z_0-9]+)", template.read_text(encoding="utf-8")))
    assert names - {"values", "get", "items"} <= {fact_id.value for fact_id in FactId}
