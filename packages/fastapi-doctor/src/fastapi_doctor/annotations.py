from pathlib import Path
from .models import Diagnostic, Severity


def format_annotation(diag: Diagnostic, scan_root: Path) -> str:
    """Format a diagnostic as a GitHub Actions workflow command annotation."""
    level = "error" if diag.severity == Severity.ERROR else "warning"
    try:
        rel = Path(diag.file_path).resolve().relative_to(scan_root.resolve())
    except ValueError:
        rel = Path(diag.file_path)
    rel_str = str(rel).replace("\\", "/")
    rule_short = diag.rule.split("/")[-1]
    return f"::{level} file={rel_str},line={diag.line},col={diag.column},title={rule_short}::{diag.message}"


def print_annotations(diagnostics: list[Diagnostic], scan_root: Path) -> int:
    """Print diagnostics as GitHub Actions annotations. Returns count printed."""
    count = 0
    for diag in diagnostics:
        print(format_annotation(diag, scan_root))
        count += 1
    return count
