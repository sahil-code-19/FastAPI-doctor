import ast

from fastapi_doctor.rules.architecture.fastt026_unused_request_param import (
    UnusedRequestParamRule,
)
from fastapi_doctor.models import Severity


def test_good_request_used_not_flagged():
    rule = UnusedRequestParamRule()
    source = """
from fastapi import FastAPI, Request
app = FastAPI()

@app.get("/info")
def get_info(request: Request):
    return {"client": request.client.host}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_no_request_param_not_flagged():
    rule = UnusedRequestParamRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/users")
def get_users():
    return []
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_unused_request_flagged():
    rule = UnusedRequestParamRule()
    source = """
from fastapi import FastAPI, Request
app = FastAPI()

@app.get("/health")
async def health(request: Request):
    return {"status": "ok"}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT026"
    assert diagnostics[0].severity == Severity.WARNING


def test_bad_unused_request_sync_flagged():
    rule = UnusedRequestParamRule()
    source = """
from fastapi import FastAPI, Request
app = FastAPI()

@app.get("/data")
def get_data(request: Request):
    return {"data": []}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1


def test_good_request_used_via_state():
    rule = UnusedRequestParamRule()
    source = """
from fastapi import FastAPI, Request
app = FastAPI()

@app.get("/tenant")
def get_tenant(request: Request):
    return {"tenant": request.state.tenant_id}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0
