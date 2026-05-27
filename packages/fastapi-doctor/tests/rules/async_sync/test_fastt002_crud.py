"""Test that FASTT002 traces imports from routers into CRUD functions."""

from pathlib import Path

from fastapi_doctor.scanner import (
    parse_file,
    scan_directory,
    trace_and_check,
    build_function_catalog,
)
from fastapi_doctor.rules.async_sync.fastt002_db_session_in_async import (
    DbSessionInAsyncRule,
)

PROJECT_DIR = Path(__file__).parent.parent.parent / "fixtures" / "fastt002_crud"


def test_crud_function_traced_from_endpoint():
    """The CRUD function has sync db.execute() — trace should find it via import."""
    rules = [DbSessionInAsyncRule()]

    parsed_files: dict[str, ast.Module] = {}
    for py_file in sorted(PROJECT_DIR.rglob("*.py")):
        tree = parse_file(py_file)
        if tree is not None:
            parsed_files[str(py_file)] = tree

    traced = trace_and_check(parsed_files, str(PROJECT_DIR), rules)

    # Should find 2 violations from create_user (execute + commit)
    # create_user_correct is not called directly from endpoints
    assert len(traced) == 2, (
        f"Expected 2 traced violation, got {len(traced)}: "
        f"{[(d.message, d.line) for d in traced]}"
    )

    for diag in traced:
        assert diag.rule == "fastapi-doctor/FASTT002"
        assert diag.severity.value == "error"


def test_full_scan_includes_traced_diagnostics():
    """Full scan_directory() should include traced CRUD violations."""
    result = scan_directory(PROJECT_DIR)

    # Find FASTT002 diagnostics from traced functions
    fastt002_diags = [
        d for d in result.diagnostics if d.rule == "fastapi-doctor/FASTT002"
    ]

    # Should have 2 from traced CRUD functions
    assert len(fastt002_diags) >= 2, (
        f"Expected at least 2 FASTT002 violations, got {len(fastt002_diags)}: "
        f"{[(d.message, d.file_path, d.line) for d in fastt002_diags]}"
    )

    # The crud file should appear in traced diagnostics
    traced_files = {d.file_path for d in fastt002_diags}
    assert any("crud" in f for f in traced_files), "CRUD file should be in diagnostics"
