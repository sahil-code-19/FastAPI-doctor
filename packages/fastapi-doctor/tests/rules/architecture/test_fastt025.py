import ast
from pathlib import Path

from fastapi_doctor.rules.architecture.fastt025_deprecated_on_event import (
    DeprecatedOnEventRule,
)
from fastapi_doctor.models import Severity

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "fastt025"


def test_good_no_diagnostics():
    rule = DeprecatedOnEventRule()
    source = (FIXTURES / "good.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "good.py", source)
    assert len(diagnostics) == 0, (
        f"Expected 0 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )


def test_bad_detects_deprecated_on_event():
    rule = DeprecatedOnEventRule()
    source = (FIXTURES / "bad.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "bad.py", source)

    assert len(diagnostics) == 2, (
        f"Expected 2 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )

    for diag in diagnostics:
        assert diag.rule == "fastapi-doctor/FASTT025"
        assert diag.severity == Severity.WARNING


def test_on_event_startup_flagged():
    rule = DeprecatedOnEventRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    pass
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1, "@app.on_event('startup') should be flagged"


def test_on_event_shutdown_flagged():
    rule = DeprecatedOnEventRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.on_event("shutdown")
async def on_shutdown():
    pass
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1, "@app.on_event('shutdown') should be flagged"


def test_lifespan_not_flagged():
    rule = DeprecatedOnEventRule()
    source = """
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "lifespan should not be flagged"


def test_regular_decorator_not_flagged():
    rule = DeprecatedOnEventRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/items")
async def get_items():
    return []
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Regular @app.get should not be flagged"
