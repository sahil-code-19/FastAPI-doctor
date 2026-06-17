from pathlib import Path
from fastapi_doctor.annotations import format_annotation, print_annotations
from fastapi_doctor.models import Diagnostic, Severity


def _diag(
    line=42,
    col=4,
    rule="fastapi-doctor/FASTT001",
    severity=Severity.ERROR,
    msg="test",
    file_path="app/routers/users.py",
):
    return Diagnostic(
        file_path=file_path,
        rule=rule,
        severity=severity,
        message=msg,
        line=line,
        column=col,
        help="",
    )


def test_error_diagnostic_formats_as_error():
    diag = _diag(severity=Severity.ERROR)
    result = format_annotation(diag, Path("/project"))
    assert result.startswith("::error file=")
    assert "line=42" in result
    assert "title=FASTT001" in result
    assert diag.message in result


def test_warning_diagnostic_formats_as_warning():
    diag = _diag(severity=Severity.WARNING)
    result = format_annotation(diag, Path("/project"))
    assert result.startswith("::warning file=")


def test_path_is_relative_to_scan_root():
    diag = _diag(file_path="/project/app/routers/users.py")
    result = format_annotation(diag, Path("/project"))
    assert "file=app/routers/users.py" in result
    assert "file=/project" not in result


def test_rule_short_name_in_title():
    diag = _diag(rule="fastapi-doctor/FASTT070")
    result = format_annotation(diag, Path("/project"))
    assert "title=FASTT070" in result
    assert "fastapi-doctor/" not in result.split("title=")[1].split("::")[0]


def test_column_included():
    diag = _diag(col=8)
    result = format_annotation(diag, Path("/project"))
    assert "col=8" in result


def test_print_annotations_returns_count(capsys):
    diags = [_diag(line=1), _diag(line=2, severity=Severity.WARNING)]
    count = print_annotations(diags, Path("/project"))
    assert count == 2
    captured = capsys.readouterr()
    assert "::error" in captured.out
    assert "::warning" in captured.out


def test_empty_diagnostics_prints_nothing(capsys):
    count = print_annotations([], Path("/project"))
    assert count == 0
    captured = capsys.readouterr()
    assert captured.out == ""


def test_path_outside_root_uses_absolute():
    diag = _diag(file_path="/completely/different/path/file.py")
    result = format_annotation(diag, Path("/project"))
    assert "file=" in result
