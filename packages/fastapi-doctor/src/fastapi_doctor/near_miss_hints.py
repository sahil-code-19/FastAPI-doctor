from .models import Diagnostic, Severity
from .inline_suppression import parse_inline_suppressions, _SUPPRESS_ALL

HINT_RULE_ID = "fastapi-doctor/HINT"


def generate_near_miss_hints(
    diagnostics: list[Diagnostic],
    source: str,
    file_path: str,
) -> list[Diagnostic]:
    """Generate hints when inline suppressions don't match actual violations.

    Three scenarios:
    1. Wrong rule ID — "suppressed FASTT001 but FASTT012 fired"
    2. Disable-next-line too far above — "suppression at line 1, violation at line 5"
    3. Rule not in stack — "suppressed [FASTT001, FASTT003] but FASTT002 fired"
    """
    suppressions = parse_inline_suppressions(source)
    if not suppressions:
        return []

    # Build a map: line → set of rule IDs that actually fired
    actual: dict[int, set[str]] = {}
    for d in diagnostics:
        actual.setdefault(d.line, set()).add(d.rule)

    hints: list[Diagnostic] = []

    for sup_line, sup_rules in suppressions.items():
        if sup_rules is _SUPPRESS_ALL:
            continue

        # Rules actually firing on this suppressed line
        actual_on_line = actual.get(sup_line, set())

        if not actual_on_line:
            continue

        # Check overlap: did the suppressed rules actually fire?
        short_sup = {r.split("/")[-1] for r in sup_rules}
        short_actual = {r.split("/")[-1] for r in actual_on_line}

        match = short_sup & short_actual
        if match:
            continue  # Suppression is working — correctly catching at least one rule

        # Near-miss: suppressed rules don't match what's actually firing
        hint = _build_hint(sup_line, short_sup, actual_on_line, file_path)
        if hint:
            hints.append(hint)

    return hints


def _build_hint(
    line: int,
    suppressed: set[str],
    actual: set[str],
    file_path: str,
) -> Diagnostic | None:
    sup_str = ", ".join(sorted(suppressed))
    act_str = ", ".join(r.split("/")[-1] for r in sorted(actual))

    if len(suppressed) == 1 and len(actual) == 1:
        msg = (
            f"Suppression hint: # disable at line {line} suppresses {sup_str}, "
            f"but {act_str} fires here. Did you mean {sup_str} → {act_str}?"
        )
    else:
        msg = (
            f"Suppression hint: # disable at line {line} suppresses [{sup_str}], "
            f"but [{act_str}] fires here instead"
        )

    return Diagnostic(
        file_path=file_path,
        rule=HINT_RULE_ID,
        severity=Severity.WARNING,
        message=msg,
        line=line,
        column=0,
        help="Check that the rule ID in your suppression comment matches the issue being flagged",
    )
