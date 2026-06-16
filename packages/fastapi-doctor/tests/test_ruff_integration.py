import json
from pathlib import Path
from fastapi_doctor.ruff_integration import (
    run_ruff_check,
    _convert_ruff_issue,
)
from fastapi_doctor.models import Severity


def test_convert_ruff_issue_error():
    issue = {
        "code": "E501",
        "message": "Line too long",
        "filename": "/project/app/routers/users.py",
        "location": {"row": 42, "column": 80},
        "fix": {"message": "Break the line"},
    }
    result = _convert_ruff_issue(issue, Path("/project"))
    assert result.rule == "ruff/E501"
    assert result.severity == Severity.ERROR
    assert result.line == 42
    assert "Break the line" in result.help


def test_convert_ruff_issue_warning():
    issue = {
        "code": "F401",
        "message": "Unused import",
        "filename": "/project/app/routers/users.py",
        "location": {"row": 1, "column": 1},
    }
    result = _convert_ruff_issue(issue, Path("/project"))
    assert result.rule == "ruff/F401"
    assert result.severity == Severity.ERROR


def test_convert_ruff_issue_unknown_rule_defaults_to_warning():
    issue = {
        "code": "ZZZ999",
        "message": "Custom rule",
        "filename": "/project/app/routers/users.py",
        "location": {"row": 10, "column": 1},
    }
    result = _convert_ruff_issue(issue, Path("/project"))
    assert result.severity == Severity.WARNING


def test_convert_ruff_issue_relative_path():
    issue = {
        "code": "I001",
        "message": "Import block is un-sorted",
        "filename": "/project/app/routers/users.py",
        "location": {"row": 3, "column": 1},
    }
    result = _convert_ruff_issue(issue, Path("/project"))
    assert result.file_path == "app/routers/users.py"


def test_ruff_not_installed_returns_empty(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda x: None)
    result = run_ruff_check([], Path("/tmp"))
    assert result == []


def test_ruff_installed_but_no_files(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/ruff")
    MonkeyRunner = type(
        "MockRunner",
        (),
        {
            "returncode": 0,
            "stdout": "[]",
        },
    )
    import fastapi_doctor.ruff_integration as ri

    original = ri.subprocess.run
    ri.subprocess.run = lambda *a, **kw: MonkeyRunner()
    result = ri.run_ruff_check([], Path("/tmp"))
    ri.subprocess.run = original
    assert result == []
