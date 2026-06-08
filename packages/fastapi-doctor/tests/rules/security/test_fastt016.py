import ast
from pathlib import Path

from fastapi_doctor.rules.security.fastt016_missing_httpsredirectmiddleware import (
    MissingHttpsRedirectMiddleware,
)
from fastapi_doctor.models import Severity

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "fastt016"


def test_good_no_diagnostics():
    rule = MissingHttpsRedirectMiddleware()
    source = (FIXTURES / "good.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "good.py", source)
    assert len(diagnostics) == 0, (
        f"Expected 0 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )


def test_bad_missing_https_redirect():
    rule = MissingHttpsRedirectMiddleware()
    source = (FIXTURES / "bad.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "bad.py", source)

    assert len(diagnostics) == 1, (
        f"Expected 1 violation, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )

    assert diagnostics[0].rule == "fastapi-doctor/FASTT016"
    assert diagnostics[0].severity == Severity.WARNING


def test_has_https_redirect_not_flagged():
    rule = MissingHttpsRedirectMiddleware()
    source = """
from fastapi import FastAPI
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()
app.add_middleware(HTTPSRedirectMiddleware)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, (
        "FastAPI with HTTPSRedirectMiddleware should not be flagged"
    )


def test_https_redirect_as_string_ok():
    rule = MissingHttpsRedirectMiddleware()
    source = """
from fastapi import FastAPI
app = FastAPI()
app.add_middleware("HTTPSRedirectMiddleware")
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "String middleware reference should be recognized"


def test_router_file_without_fastapi_not_flagged():
    rule = MissingHttpsRedirectMiddleware()
    source = """
from fastapi import APIRouter
router = APIRouter()

@router.get("/items")
def get_items():
    return []
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Files without FastAPI should not be flagged"
