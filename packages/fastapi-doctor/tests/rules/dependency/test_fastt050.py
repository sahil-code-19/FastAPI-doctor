import ast

from fastapi_doctor.rules.dependency.fastt050_get_db_without_try_finally import (
    GetDbWithoutTryFinallyRule,
)
from fastapi_doctor.models import Severity


def test_good_with_try_finally_not_flagged():
    rule = GetDbWithoutTryFinallyRule()
    source = """
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_no_yield_not_flagged():
    rule = GetDbWithoutTryFinallyRule()
    source = """
def calculate(x: int) -> int:
    return x * 2
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_yield_without_try_finally_flagged():
    rule = GetDbWithoutTryFinallyRule()
    source = """
def get_db():
    db = SessionLocal()
    yield db
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT050"
    assert diagnostics[0].severity == Severity.ERROR


def test_bad_yield_with_try_no_finally_flagged():
    rule = GetDbWithoutTryFinallyRule()
    source = """
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        pass
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1


def test_bad_async_yield_without_try_flagged():
    rule = GetDbWithoutTryFinallyRule()
    source = """
async def get_db():
    db = AsyncSessionLocal()
    yield db
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
