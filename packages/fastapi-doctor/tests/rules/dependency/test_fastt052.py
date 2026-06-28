import ast

from fastapi_doctor.rules.dependency.fastt052_session_without_yield import (
    SessionWithoutYieldRule,
)
from fastapi_doctor.models import Severity


def test_good_session_with_yield_not_flagged():
    rule = SessionWithoutYieldRule()
    source = """
def get_db():
    db = SessionLocal()
    yield db
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_no_session_not_flagged():
    rule = SessionWithoutYieldRule()
    source = """
def compute():
    result = 2 + 2
    return result
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_session_return_flagged():
    rule = SessionWithoutYieldRule()
    source = """
def get_db():
    db = SessionLocal()
    return db
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT052"
    assert diagnostics[0].severity == Severity.WARNING


def test_good_no_session_in_name_not_flagged():
    rule = SessionWithoutYieldRule()
    source = """
def get_db():
    conn = get_connection()
    return conn
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_session_return_no_yield_flagged():
    rule = SessionWithoutYieldRule()
    source = """
def get_db():
    db = AsyncSessionLocal()
    return db
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
