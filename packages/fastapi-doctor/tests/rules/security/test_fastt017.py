import ast
from pathlib import Path

from fastapi_doctor.rules.security.fastt017_sql_fstring_injection import (
    SqlFStringInjectionRule,
)
from fastapi_doctor.models import Severity

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "fastt017"


def test_good_no_diagnostics():
    rule = SqlFStringInjectionRule()
    source = (FIXTURES / "good.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "good.py", source)
    assert len(diagnostics) == 0, (
        f"Expected 0 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )


def test_bad_detects_sql_fstring():
    rule = SqlFStringInjectionRule()
    source = (FIXTURES / "bad.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "bad.py", source)

    assert len(diagnostics) == 5, (
        f"Expected 5 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )

    for diag in diagnostics:
        assert diag.rule == "fastapi-doctor/FASTT017"
        assert diag.severity == Severity.ERROR


def test_select_fstring_flagged():
    rule = SqlFStringInjectionRule()
    source = 'query = f"SELECT * FROM users WHERE id = {uid}"'
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1, "SELECT f-string should be flagged"


def test_insert_fstring_flagged():
    rule = SqlFStringInjectionRule()
    source = 'query = f"INSERT INTO users VALUES ({name})"'
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1, "INSERT f-string should be flagged"


def test_non_sql_fstring_not_flagged():
    rule = SqlFStringInjectionRule()
    source = 'msg = f"User {uid} logged in"'
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Non-SQL f-string should not be flagged"


def test_static_sql_not_flagged():
    rule = SqlFStringInjectionRule()
    source = 'db.execute("SELECT * FROM users")'
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Static SQL string should not be flagged"


def test_parameterized_sql_not_flagged():
    rule = SqlFStringInjectionRule()
    source = 'db.execute("SELECT * FROM users WHERE id = :id", {"id": 5})'
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Parameterized SQL should not be flagged"
