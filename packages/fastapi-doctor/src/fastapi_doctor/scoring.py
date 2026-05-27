from .models import Diagnostic, ScoreResult, Severity


def calculate_score(diagnostics: list[Diagnostic]) -> ScoreResult:
    """
    Calculate health score from diagnostics.
    Formula: 100 - (unique_error_rules x 1.5) - (unique_warning_rules x 0.75)
    """
    unique_error_rules: set[str] = set()
    unique_warning_rules: set[str] = set()

    for diag in diagnostics:
        if diag.severity == Severity.ERROR:
            unique_error_rules.add(diag.rule)
        else:
            unique_warning_rules.add(diag.rule)

    score = 100
    score -= len(unique_error_rules) * 1.5
    score -= len(unique_warning_rules) * 0.75

    # Clamp to 0-100
    score = max(0, min(100, score))
    score = round(score)

    # Determine label
    if score >= 75:
        label = "Great"
    elif score >= 50:
        label = "Needs work"
    else:
        label = "Critical"

    return ScoreResult(score=score, label=label)
