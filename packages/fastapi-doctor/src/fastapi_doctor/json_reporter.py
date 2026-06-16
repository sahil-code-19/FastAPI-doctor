import json
from .models import Diagnostic, ScanResult, Severity

SCHEMA_VERSION = 1


def format_json(
    result: ScanResult,
    directory: str,
    mode: str,
    version: str,
    base_branch: str | None = None,
    ok: bool = True,
    error: dict | None = None,
) -> str:
    """Format scan results as a JSON report matching the schema."""
    diagnostics_json = [_diagnostic_to_dict(d) for d in result.diagnostics]

    errors = sum(1 for d in result.diagnostics if d.severity == Severity.ERROR)
    warnings = sum(1 for d in result.diagnostics if d.severity == Severity.WARNING)

    affected_files = len({d.file_path for d in result.diagnostics})

    report = {
        "schemaVersion": SCHEMA_VERSION,
        "version": version,
        "ok": ok,
        "directory": directory,
        "mode": mode,
        "diff": {
            "baseBranch": base_branch or "",
            "currentBranch": "",
            "changedFileCount": result.files_scanned if mode == "diff" else 0,
            "isCurrentChanges": False,
        }
        if mode == "diff"
        else None,
        "diagnostics": diagnostics_json,
        "summary": {
            "errorCount": errors,
            "warningCount": warnings,
            "affectedFileCount": affected_files,
            "totalDiagnosticCount": len(result.diagnostics),
        },
        "elapsedMilliseconds": round(result.elapsed_ms, 1),
        "error": error,
    }

    return json.dumps(report, indent=2, ensure_ascii=False)


def format_json_compact(
    result: ScanResult,
    directory: str,
    mode: str,
    version: str,
    ok: bool = True,
    error: dict | None = None,
) -> str:
    """Format scan results as a compact (single-line) JSON report."""
    return format_json(result, directory, mode, version, ok=ok, error=error).replace(
        "\n", ""
    )


def format_error_json(
    error_message: str,
    directory: str,
    mode: str,
    version: str,
    exception_type: str = "InternalError",
) -> str:
    """Format an error as a JSON report."""
    report = {
        "schemaVersion": SCHEMA_VERSION,
        "version": version,
        "ok": False,
        "directory": directory,
        "mode": mode,
        "diff": None,
        "diagnostics": [],
        "summary": {
            "errorCount": 0,
            "warningCount": 0,
            "affectedFileCount": 0,
            "totalDiagnosticCount": 0,
        },
        "elapsedMilliseconds": 0,
        "error": {
            "type": exception_type,
            "message": error_message,
        },
    }
    return json.dumps(report, indent=2, ensure_ascii=False)


def _diagnostic_to_dict(d: Diagnostic) -> dict:
    return {
        "filePath": d.file_path,
        "plugin": "fastapi-doctor",
        "rule": d.rule.split("/")[-1] if "/" in d.rule else d.rule,
        "fullRule": d.rule,
        "severity": d.severity.value,
        "message": d.message,
        "help": d.help,
        "line": d.line,
        "column": d.column,
    }
