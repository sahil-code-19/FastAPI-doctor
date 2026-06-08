import ast
from pathlib import Path

from fastapi_doctor.rules.security.fastt013_hardcoded_secrets import (
    HardcodedSecretsRule,
)
from fastapi_doctor.models import Severity

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "fastt013"


def test_good_no_diagnostics():
    rule = HardcodedSecretsRule()
    source = (FIXTURES / "good.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "good.py", source)
    assert len(diagnostics) == 0, (
        f"Expected 0 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )


def test_bad_detects_secrets():
    rule = HardcodedSecretsRule()
    source = (FIXTURES / "bad.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "bad.py", source)

    assert len(diagnostics) > 0, (
        f"Expected violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )

    for diag in diagnostics:
        assert diag.rule == "fastapi-doctor/FASTT013"

    # Errors and warnings should both appear
    errors = [d for d in diagnostics if d.severity == Severity.ERROR]
    warnings = [d for d in diagnostics if d.severity == Severity.WARNING]
    assert len(errors) >= 10, (
        f"Expected at least 10 errors (AST + regex), got {len(errors)}"
    )
    assert len(warnings) >= 3, (
        f"Expected at least 3 warnings (placeholders), got {len(warnings)}"
    )


def test_os_environ_skipped():
    rule = HardcodedSecretsRule()
    source = "SECRET_KEY = os.environ.get('SECRET_KEY')"
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "os.environ should be skipped"


def test_os_getenv_skipped():
    rule = HardcodedSecretsRule()
    source = "TOKEN = os.getenv('TOKEN')"
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "os.getenv should be skipped"


def test_settings_skipped():
    rule = HardcodedSecretsRule()
    source = "SECRET_KEY = settings.SECRET_KEY"
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "settings.X should be skipped"


def test_placeholder_warning():
    rule = HardcodedSecretsRule()
    source = "API_KEY = ''\nSECRET_KEY = 'changeme'"
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 2
    for d in diagnostics:
        assert d.severity == Severity.WARNING
        assert d.rule == "fastapi-doctor/FASTT013"


def test_short_string_skipped():
    rule = HardcodedSecretsRule()
    source = 'DEBUG = "true"\nPAGE_SIZE = "20"'
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Short strings should not be flagged"


def test_non_secret_name_skipped():
    rule = HardcodedSecretsRule()
    source = 'APP_NAME = "job-board"\nVERSION = "0.1.0"'
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Non-secret variable names should be skipped"


def test_urls_skipped():
    rule = HardcodedSecretsRule()
    source = 'API_URL = "https://api.example.com/v1"'
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "URLs should not be flagged"


def test_regex_github_token_detected():
    rule = HardcodedSecretsRule()
    # Not a secret-named variable, but the value matches a known pattern
    source = 'SOME_VAR = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"'
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1, "GitHub token pattern should be detected"
    assert "GitHub" in diagnostics[0].message


def test_os_environ_subscript_skipped():
    rule = HardcodedSecretsRule()
    source = 'API_KEY = os.environ["API_KEY"]'
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "os.environ['KEY'] should be skipped"
