from .models import Diagnostic, ScoreResult, Severity

# ANSI colors
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
GRAY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_header(version: str):
    print(f"{BOLD}FastAPI Therapist{RESET} v{version}")
    print()


def print_diagnostics(diagnostics: list[Diagnostic], verbose: bool = False):
    if not diagnostics:
        print(f"{GREEN}No issues found!{RESET}")
        return

    # Group by rule + severity so mixed-severity rules get separate headers
    by_rule_severity: dict[tuple[str, str], list[Diagnostic]] = {}
    for diag in diagnostics:
        key = (diag.rule, diag.severity.value)
        by_rule_severity.setdefault(key, []).append(diag)

    for (rule, severity_value), rule_diags in by_rule_severity.items():
        is_error = severity_value == Severity.ERROR.value
        severity_icon = "X" if is_error else "!"
        color = RED if is_error else YELLOW

        print(f"  {color}{severity_icon} {rule}{RESET} ({len(rule_diags)} issues)")

        for diag in rule_diags:
            print(
                f"    {color}→{RESET} {GRAY}{diag.file_path}:{diag.line}{RESET}  {diag.message}"
            )

        if rule_diags[0].help:
            print(f"    {GRAY}-> {rule_diags[0].help}{RESET}")

        print()


def print_score(score_result: ScoreResult):
    color = (
        GREEN
        if score_result.score >= 75
        else YELLOW
        if score_result.score >= 50
        else RED
    )
    print(
        f"{BOLD}Score:{RESET} {color}{score_result.score}/100{RESET} ({score_result.label})"
    )


def print_summary(diagnostics: list[Diagnostic], files_scanned: int, elapsed_ms: float):
    errors = sum(1 for d in diagnostics if d.severity == Severity.ERROR)
    warnings = sum(1 for d in diagnostics if d.severity == Severity.WARNING)
    print(f"{GRAY}Scanned {files_scanned} files in {elapsed_ms:.0f}ms{RESET}")
    if diagnostics:
        print(f"{GRAY}{errors} errors, {warnings} warnings{RESET}")
