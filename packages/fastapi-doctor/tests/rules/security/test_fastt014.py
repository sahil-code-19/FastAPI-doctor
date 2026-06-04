import ast
from pathlib import Path

from fastapi_doctor.rules.security.fastt014_debugtrue_non_testfile import (
    DebugTrueNonTestFile,
)
from fastapi_doctor.models import Severity

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "fastt014"


def test_good_no_diagnostics():
    rule = DebugTrueNonTestFile()
    source = (FIXTURES / "good.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "good.py", source)
    assert len(diagnostics) == 0, (
        f"Expected 0 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )


def test_bad_detects_debug_true():
    rule = DebugTrueNonTestFile()
    source = (FIXTURES / "bad.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "bad.py", source)

    assert len(diagnostics) == 4, (
        f"Expected 4 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )

    for diag in diagnostics:
        assert diag.rule == "fastapi-doctor/FASTT014"
        assert diag.severity == Severity.WARNING


def test_fastapi_constructor_flagged():
    rule = DebugTrueNonTestFile()
    source = """
from fastapi import FastAPI
app = FastAPI(debug=True)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1, "FastAPI(debug=True) should be flagged"


def test_uvicorn_run_flagged():
    rule = DebugTrueNonTestFile()
    source = """
import uvicorn
uvicorn.run("app:app", debug=True)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1, "uvicorn.run(debug=True) should be flagged"


def test_debug_false_not_flagged():
    rule = DebugTrueNonTestFile()
    source = """
from fastapi import FastAPI
import uvicorn
app = FastAPI(debug=False)
uvicorn.run("app:app", debug=False)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "debug=False should not be flagged"


def test_no_debug_not_flagged():
    rule = DebugTrueNonTestFile()
    source = """
from fastapi import FastAPI
import uvicorn
app = FastAPI()
uvicorn.run("app:app")
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "No debug arg should not be flagged"


def test_other_function_debug_true_not_flagged():
    rule = DebugTrueNonTestFile()
    source = """
def my_func(debug=True):
    pass
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Only FastAPI() and uvicorn.run() should be checked"
