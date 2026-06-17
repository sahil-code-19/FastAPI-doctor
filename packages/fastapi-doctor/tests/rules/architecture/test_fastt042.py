import ast

from fastapi_doctor.rules.architecture.fastt042_dict_instead_of_model_dump import (
    DictInsteadOfModelDumpRule,
)
from fastapi_doctor.models import Severity


def test_good_model_dump_not_flagged():
    rule = DictInsteadOfModelDumpRule()
    source = """
from pydantic import BaseModel

class User(BaseModel):
    name: str

user = User(name="test")
data = user.model_dump()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_json_loads_not_flagged():
    rule = DictInsteadOfModelDumpRule()
    source = """
import json
data = json.loads('{"key": "value"}')
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_dict_model_flagged():
    rule = DictInsteadOfModelDumpRule()
    source = """
from pydantic import BaseModel

class User(BaseModel):
    name: str

user = User(name="test")
data = dict(user)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT042"
    assert diagnostics[0].severity == Severity.WARNING


def test_bad_dict_empty_call_not_flagged():
    rule = DictInsteadOfModelDumpRule()
    source = """
d = dict()
d["key"] = "value"
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_dict_model_in_route_flagged():
    rule = DictInsteadOfModelDumpRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/user")
def get_user():
    user = get_user_from_db()
    return dict(user)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
