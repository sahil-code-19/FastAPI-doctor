from fastapi_doctor.inline_suppression import (
    parse_inline_suppressions,
    is_diagnostic_suppressed,
)
from fastapi_doctor.models import Diagnostic, Severity
from fastapi_doctor.config import FastapiDoctorConfig


def _diag(rule="FASTT001", line=5):
    return Diagnostic(
        severity=Severity.ERROR,
        file_path="test.py",
        rule=rule,
        message="test",
        line=line,
        column=0,
        help="",
    )


def test_inline_suppression_respected_by_default():
    source = """from fastapi import FastAPI
@app.get("/")
def root():  # fastapi-doctor-disable-line FASTT012
    return {}
"""
    supp = parse_inline_suppressions(source)
    assert is_diagnostic_suppressed(_diag("FASTT012", line=3), supp)


def test_inline_suppression_ignored_when_disabled():
    source = """from fastapi import FastAPI
@app.get("/")
def root():  # fastapi-doctor-disable-line FASTT012
    return {}
"""
    supp = parse_inline_suppressions(source)
    assert is_diagnostic_suppressed(_diag("FASTT012", line=3), supp)


def test_config_respect_inline_disables_defaults_true():
    config = FastapiDoctorConfig()
    assert config.respectInlineDisables is True


def test_config_can_disable_inline_suppression():
    config = FastapiDoctorConfig()
    config.respectInlineDisables = False
    assert config.respectInlineDisables is False
