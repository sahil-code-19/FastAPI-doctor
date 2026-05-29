import ast
from pathlib import Path

from fastapi_doctor.rules.correctness.fastt070_missing_status_code import (
    MissingStatusCodeRule,
)

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "fastt070"


def test_good_endpoints_no_diagnostics():
    rule = MissingStatusCodeRule()
    source = (FIXTURES / "good.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "good.py", source)
    assert len(diagnostics) == 0, (
        f"Expected 0 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )


def test_bad_endpoints_detected():
    rule = MissingStatusCodeRule()
    source = (FIXTURES / "bad.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "bad.py", source)
    assert len(diagnostics) == 4, (
        f"Expected 4 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )

    for diag in diagnostics:
        assert diag.rule == "fastapi-doctor/FASTT070"
        assert diag.severity.value == "warning"


def test_get_endpoint_ignored():
    rule = MissingStatusCodeRule()
    source = """
from fastapi import FastAPI

app = FastAPI()

@app.get("/items")
async def get_items():
    return []
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "GET endpoints should not be flagged"
