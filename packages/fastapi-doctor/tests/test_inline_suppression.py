from fastapi_doctor.inline_suppression import (
    parse_inline_suppressions,
    is_diagnostic_suppressed,
)
from fastapi_doctor.models import Diagnostic, Severity


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


def test_disable_line_specific_rule():
    source = """from fastapi import FastAPI
app = FastAPI()
@app.get("/")
def root():
    return {}  # fastapi-doctor-disable-line FASTT012
"""
    supp = parse_inline_suppressions(source)
    d = _diag("FASTT012", line=5)
    assert is_diagnostic_suppressed(d, supp), "FASTT012 should be suppressed on line 5"


def test_disable_line_wrong_rule_not_suppressed():
    source = """from fastapi import FastAPI
@app.get("/")
def root():
    return {}  # fastapi-doctor-disable-line FASTT012
"""
    supp = parse_inline_suppressions(source)
    d = _diag("FASTT001", line=5)
    assert not is_diagnostic_suppressed(d, supp), "FASTT001 should NOT be suppressed"


def test_disable_line_all_rules():
    source = """from fastapi import FastAPI
@app.get("/")
def root():
    return {}  # fastapi-doctor-disable-line
"""
    supp = parse_inline_suppressions(source)
    d = _diag("FASTT012", line=4)
    assert is_diagnostic_suppressed(d, supp), "Empty comment should suppress ALL rules"


def test_disable_next_line_single_rule():
    source = """# fastapi-doctor-disable-next-line FASTT012
@app.get("/")
def root():
    return {}
"""
    supp = parse_inline_suppressions(source)
    d = _diag("FASTT012", line=3)
    assert is_diagnostic_suppressed(d, supp), (
        "Suppresses on function def after decorator"
    )


def test_disable_next_line_different_rule_not_suppressed():
    source = """# fastapi-doctor-disable-next-line FASTT012
@app.get("/")
def root():
    return {}
"""
    supp = parse_inline_suppressions(source)
    d = _diag("FASTT001", line=3)
    assert not is_diagnostic_suppressed(d, supp), "Wrong rule should not be suppressed"


def test_disable_next_line_stacked():
    source = """# fastapi-doctor-disable-next-line FASTT012
# fastapi-doctor-disable-next-line FASTT003
@app.get("/")
def root():
    return {}
"""
    supp = parse_inline_suppressions(source)
    assert is_diagnostic_suppressed(_diag("FASTT012", line=4), supp)
    assert is_diagnostic_suppressed(_diag("FASTT003", line=4), supp)
    assert not is_diagnostic_suppressed(_diag("FASTT001", line=4), supp)


def test_disable_next_line_stacking_broken_by_blank():
    source = """# fastapi-doctor-disable-next-line FASTT012

# fastapi-doctor-disable-next-line FASTT003
@app.get("/")
def root():
    return {}
"""
    supp = parse_inline_suppressions(source)
    # First comment applies (sup at line 5). Second comment applies too (sup at line 5).
    # But they don't stack — second replaces first because blank line breaks chain
    assert not is_diagnostic_suppressed(_diag("FASTT012", line=5), supp), (
        "FASTT012 chain broken by blank, should NOT be suppressed"
    )
    assert is_diagnostic_suppressed(_diag("FASTT003", line=5), supp), (
        "FASTT003 should still be suppressed (latest comment)"
    )


def test_disable_next_line_no_code_to_suppress():
    source = """# fastapi-doctor-disable-next-line FASTT012
"""
    supp = parse_inline_suppressions(source)
    assert len(supp) == 0, "No code line to suppress means no suppression entry"


def test_multi_line_decorator_targets_function():
    source = """# fastapi-doctor-disable-next-line FASTT070
@router.post(
    "/{id}/status",
    response_model=ApplicationResponse
)
async def update_status(id: int, db: AsyncSession = Depends(get_db)):
    app_obj = await db.get(Application, id)
    return ApplicationResponse.model_validate(app_obj)
"""
    supp = parse_inline_suppressions(source)
    d = _diag("FASTT070", line=6)
    assert is_diagnostic_suppressed(d, supp), (
        "disable-next-line should target function def across multi-line decorator"
    )
