import json
from fastapi_doctor.json_reporter import (
    format_json,
    format_json_compact,
    format_error_json,
)
from fastapi_doctor.models import Diagnostic, ScanResult, Severity


def _sample_diag():
    return Diagnostic(
        file_path="app/routers/users.py",
        rule="fastapi-doctor/FASTT001",
        severity=Severity.ERROR,
        message="Synchronous requests.get() inside async endpoint",
        line=42,
        column=4,
        help="Use httpx.AsyncClient or wrap in asyncio.to_thread()",
    )


def _sample_result():
    return ScanResult(
        diagnostics=[_sample_diag()],
        files_scanned=10,
        elapsed_ms=1234.5,
        mode="full",
    )


def test_format_json_has_required_fields():
    result = _sample_result()
    output = format_json(result, "/path/to/project", "full", "0.3.0")
    data = json.loads(output)

    assert data["schemaVersion"] == 1
    assert data["version"] == "0.3.0"
    assert data["ok"] is True
    assert data["directory"] == "/path/to/project"
    assert data["mode"] == "full"
    assert len(data["diagnostics"]) == 1
    assert data["summary"]["errorCount"] == 1
    assert data["summary"]["warningCount"] == 0


def test_format_json_diagnostic_fields():
    result = _sample_result()
    output = format_json(result, "/path", "full", "0.3.0")
    data = json.loads(output)
    diag = data["diagnostics"][0]

    assert diag["filePath"] == "app/routers/users.py"
    assert diag["rule"] == "FASTT001"
    assert diag["fullRule"] == "fastapi-doctor/FASTT001"
    assert diag["severity"] == "error"
    assert diag["line"] == 42
    assert diag["column"] == 4


def test_format_json_compact_single_line():
    result = _sample_result()
    output = format_json_compact(result, "/path", "full", "0.3.0")
    assert "\n" not in output
    data = json.loads(output)
    assert data["mode"] == "full"


def test_format_json_with_diff_mode():
    result = _sample_result()
    result.mode = "diff"
    output = format_json(result, "/path", "diff", "0.3.0", base_branch="main")
    data = json.loads(output)

    assert data["mode"] == "diff"
    assert data["diff"] is not None
    assert data["diff"]["baseBranch"] == "main"
    assert data["diff"]["changedFileCount"] == 10


def test_format_json_without_diff_mode():
    result = _sample_result()
    output = format_json(result, "/path", "full", "0.3.0")
    data = json.loads(output)

    assert data["diff"] is None


def test_format_error_json():
    output = format_error_json("Something broke", "/path", "full", "0.3.0")
    data = json.loads(output)

    assert data["ok"] is False
    assert data["error"]["type"] == "InternalError"
    assert data["error"]["message"] == "Something broke"
    assert data["diagnostics"] == []
    assert data["summary"]["totalDiagnosticCount"] == 0


def test_format_error_json_custom_type():
    output = format_error_json(
        "Timeout", "/path", "diff", "0.3.0", exception_type="TimeoutError"
    )
    data = json.loads(output)

    assert data["error"]["type"] == "TimeoutError"
    assert data["mode"] == "diff"


def test_format_json_multiple_severity():
    d1 = Diagnostic(
        file_path="a.py",
        rule="FASTT001",
        severity=Severity.ERROR,
        message="e1",
        line=1,
        column=1,
    )
    d2 = Diagnostic(
        file_path="b.py",
        rule="FASTT012",
        severity=Severity.WARNING,
        message="w1",
        line=2,
        column=2,
    )
    result = ScanResult(
        diagnostics=[d1, d2], files_scanned=5, elapsed_ms=500, mode="full"
    )

    output = format_json(result, "/x", "full", "0.3.0")
    data = json.loads(output)

    assert data["summary"]["errorCount"] == 1
    assert data["summary"]["warningCount"] == 1
    assert data["summary"]["affectedFileCount"] == 2
    assert data["summary"]["totalDiagnosticCount"] == 2
