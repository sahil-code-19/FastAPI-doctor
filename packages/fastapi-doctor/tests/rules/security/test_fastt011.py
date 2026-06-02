import ast
from pathlib import Path

from fastapi_doctor.rules.security.fastt011_response_model_none import (
    ResponseModelNoneRule,
)
from fastapi_doctor.models import Severity

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "fastt011"


def test_good_no_diagnostics():
    rule = ResponseModelNoneRule()
    source = (FIXTURES / "good.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "good.py", source)
    assert len(diagnostics) == 0, (
        f"Expected 0 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )


def test_bad_detects_response_model_none():
    rule = ResponseModelNoneRule()
    source = (FIXTURES / "bad.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "bad.py", source)

    assert len(diagnostics) == 3, (
        f"Expected 3 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )

    for diag in diagnostics:
        assert diag.rule == "fastapi-doctor/FASTT011"
        assert diag.severity == Severity.ERROR


def test_sensitive_dict_return_flagged():
    rule = ResponseModelNoneRule()
    source = """
from fastapi import FastAPI

app = FastAPI()

@app.post("/login", response_model=None)
async def login():
    return {"token": "abc", "password": "secret"}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1, "Dict with 'token' key should be flagged"


def test_non_sensitive_dict_not_flagged():
    rule = ResponseModelNoneRule()
    source = """
from fastapi import FastAPI

app = FastAPI()

@app.post("/items", response_model=None)
async def create():
    return {"status": "ok", "id": 1}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Dict without sensitive keys should not be flagged"


def test_db_sourced_var_flagged():
    rule = ResponseModelNoneRule()
    source = """
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

app = FastAPI()

@app.get("/users/{id}", response_model=None)
async def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(User).first()
    return user
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1, (
        "DB-sourced variable with response_model=None should be flagged"
    )


def test_no_response_model_none_not_flagged():
    rule = ResponseModelNoneRule()
    source = """
from fastapi import FastAPI

app = FastAPI()

@app.post("/login")
async def login():
    return {"token": "abc"}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Without response_model=None should not be flagged"
