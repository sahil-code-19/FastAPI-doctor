import json
import shutil
import subprocess
from pathlib import Path
from .models import Diagnostic, Severity


def run_ruff_check(files: list[Path], scan_root: Path) -> list[Diagnostic]:
    """Run ruff check on given files and convert to Diagnostic list.

    Returns empty list if ruff is not installed or no issues found.
    """
    # Try direct ruff CLI first, then uv run ruff (for venv-local installs)
    ruff_cmd = _find_ruff(scan_root)
    if not ruff_cmd:
        return []

    cmd = ruff_cmd + ["check", "--output-format", "json"]
    cmd += [str(f) for f in files]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=scan_root, timeout=60
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return []

    if result.returncode not in (0, 1):
        return []

    try:
        issues = json.loads(result.stdout) if result.stdout.strip() else []
    except json.JSONDecodeError:
        return []

    return [_convert_ruff_issue(i, scan_root) for i in issues]


def _find_ruff(scan_root: Path) -> list[str] | None:
    """Find ruff executable — direct PATH or project venv via uv."""
    if shutil.which("ruff"):
        return ["ruff"]

    uv = shutil.which("uv")
    if uv:
        try:
            result = subprocess.run(
                [uv, "run", "ruff", "--version"],
                capture_output=True,
                text=True,
                cwd=scan_root,
                timeout=10,
            )
            if result.returncode == 0:
                return [uv, "run", "ruff"]
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

    return None


def _ruff_severity(code: str) -> Severity:
    """Map ruff rule code to our severity. E/F are errors, everything else is warning."""
    if len(code) >= 1 and code[0] in ("E", "F"):
        return Severity.ERROR
    return Severity.WARNING


def _convert_ruff_issue(issue: dict, scan_root: Path) -> Diagnostic:
    code = issue.get("code", "unknown")
    severity = _ruff_severity(code)
    try:
        file_path = Path(issue["filename"]).relative_to(scan_root.resolve())
    except (ValueError, KeyError):
        file_path = Path(issue.get("filename", "unknown"))

    return Diagnostic(
        file_path=str(file_path),
        rule=f"ruff/{code}",
        severity=severity,
        message=issue.get("message", "ruff linting issue"),
        line=issue["location"]["row"],
        column=issue["location"]["column"],
        help=f"Fix: {issue.get('fix', {}).get('message', '')}"
        if issue.get("fix")
        else "",
    )
