from .models import Diagnostic, ScoreResult, Severity

# ANSI colors
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
GRAY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_header(version: str):
    print(f"{BOLD}FastAPI Doctor{RESET} v{version}")
    print()


def print_diagnostics(diagnostics: list[Diagnostic], verbose: bool = False):
    if not diagnostics:
        print(f"{GREEN}No issues found!{RESET}")
        return

    # Group by rule
    by_rule: dict[str, list[Diagnostic]] = {}
    for diag in diagnostics:
        by_rule.setdefault(diag.rule, []).append(diag)

    for rule, rule_diags in by_rule.items():
        severity_icon = "X" if rule_diags[0].severity == Severity.ERROR else "!"
        color = RED if rule_diags[0].severity == Severity.ERROR else YELLOW

        print(f"  {color}{severity_icon} {rule}{RESET} ({len(rule_diags)} issues)")
        print(f"    {GRAY}{rule_diags[0].message}{RESET}")

        if rule_diags[0].help:
            print(f"    {GRAY}-> {rule_diags[0].help}{RESET}")

        if verbose:
            for diag in rule_diags:
                print(f"    {GRAY}{diag.file_path}:{diag.line}{RESET}")
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
