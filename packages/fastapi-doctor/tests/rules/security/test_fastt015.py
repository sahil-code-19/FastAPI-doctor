import ast
from pathlib import Path

from fastapi_doctor.rules.security.fastt015_cors_wildcard_credentials import (
    CorsWildcardCredentialsRule,
)
from fastapi_doctor.models import Severity

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "fastt015"


def test_good_no_diagnostics():
    rule = CorsWildcardCredentialsRule()
    source = (FIXTURES / "good.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "good.py", source)
    assert len(diagnostics) == 0, (
        f"Expected 0 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )


def test_bad_detects_wildcard_credentials():
    rule = CorsWildcardCredentialsRule()
    source = (FIXTURES / "bad.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "bad.py", source)

    assert len(diagnostics) == 3, (
        f"Expected 3 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )

    for diag in diagnostics:
        assert diag.rule == "fastapi-doctor/FASTT015"
        assert diag.severity == Severity.ERROR


def test_cors_class_middleware_flagged():
    rule = CorsWildcardCredentialsRule()
    source = """
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1, (
        "CORSMiddleware class with wildcard+credentials should be flagged"
    )


def test_cors_string_middleware_flagged():
    rule = CorsWildcardCredentialsRule()
    source = """
app = FastAPI()
app.add_middleware("CORSMiddleware", allow_origins=["*"], allow_credentials=True)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1, (
        "CORSMiddleware string with wildcard+credentials should be flagged"
    )


def test_fastapi_constructor_flagged():
    rule = CorsWildcardCredentialsRule()
    source = """
from fastapi import FastAPI
app = FastAPI(allow_origins=["*"], allow_credentials=True)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1, (
        "FastAPI constructor with wildcard+credentials should be flagged"
    )


def test_wildcard_without_credentials_not_flagged():
    rule = CorsWildcardCredentialsRule()
    source = """
app.add_middleware(CORSMiddleware, allow_origins=["*"])
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Wildcard without credentials should not be flagged"


def test_credentials_without_wildcard_not_flagged():
    rule = CorsWildcardCredentialsRule()
    source = """
app.add_middleware(CORSMiddleware, allow_origins=["https://example.com"], allow_credentials=True)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Credentials without wildcard should not be flagged"
