from fastapi_doctor.near_miss_hints import generate_near_miss_hints, HINT_RULE_ID
from fastapi_doctor.models import Diagnostic, Severity


def _diag(rule="fastapi-doctor/FASTT012", line=5, msg="test"):
    return Diagnostic(
        file_path="t.py",
        rule=rule,
        severity=Severity.WARNING,
        message=msg,
        line=line,
        column=0,
        help="",
    )


def test_wrong_rule_id_hint_generated():
    source = """@app.get("/")
def root():
    return {}  # fastapi-doctor-disable-line FASTT001
"""
    diags = [_diag("fastapi-doctor/FASTT012", line=3)]
    hints = generate_near_miss_hints(diags, source, "t.py")
    assert len(hints) == 1
    assert hints[0].rule == HINT_RULE_ID
    assert "FASTT001" in hints[0].message
    assert "FASTT012" in hints[0].message


def test_no_hint_when_suppression_matches():
    source = """@app.get("/")
def root():
    return {}  # fastapi-doctor-disable-line FASTT012
"""
    diags = [_diag("fastapi-doctor/FASTT012", line=3)]
    hints = generate_near_miss_hints(diags, source, "t.py")
    assert len(hints) == 0, "Matching suppression should not generate hint"


def test_no_hint_when_no_suppression():
    source = "@app.get('/')\ndef root():\n    return {}"
    diags = [_diag("fastapi-doctor/FASTT012", line=2)]
    hints = generate_near_miss_hints(diags, source, "t.py")
    assert len(hints) == 0


def test_no_hint_for_suppress_all():
    source = """@app.get("/")
def root():
    return {}  # fastapi-doctor-disable-line
"""
    diags = [_diag("fastapi-doctor/FASTT012", line=3)]
    hints = generate_near_miss_hints(diags, source, "t.py")
    assert len(hints) == 0, "Suppress-all should not generate hints"


def test_no_hint_when_no_diagnostics_on_line():
    source = """@app.get("/")
def root():
    return {}  # fastapi-doctor-disable-line FASTT001
"""
    diags = [_diag("fastapi-doctor/FASTT012", line=10)]  # different line
    hints = generate_near_miss_hints(diags, source, "t.py")
    assert len(hints) == 0, "No actual diag on suppressed line → no hint"


def test_multiple_actual_rules_on_same_line():
    source = """@app.get("/")
def root():
    return {}  # fastapi-doctor-disable-line FASTT001
"""
    diags = [
        _diag("fastapi-doctor/FASTT012", line=3),
        _diag("fastapi-doctor/FASTT003", line=3),
    ]
    hints = generate_near_miss_hints(diags, source, "t.py")
    assert len(hints) == 1
    assert "FASTT012" in hints[0].message
    assert "FASTT003" in hints[0].message


def test_no_hint_for_disable_next_line_correct():
    source = """# fastapi-doctor-disable-next-line FASTT012
@app.get("/")
def root():
    return {}
"""
    diags = [_diag("fastapi-doctor/FASTT012", line=4)]  # function def line
    hints = generate_near_miss_hints(diags, source, "t.py")
    assert len(hints) == 0, "Correct disable-next-line target should not hint"
