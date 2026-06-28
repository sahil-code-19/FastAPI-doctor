import ast

from fastapi_doctor.rules.pydantic.fastt043_raw_dict_with_response_model import (
    RawDictWithResponseModelRule,
)
from fastapi_doctor.models import Severity


def test_good_return_model_instance_not_flagged():
    rule = RawDictWithResponseModelRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/user", response_model=UserSchema)
def get_user():
    user = UserSchema(name="test")
    return user
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_dict_return_without_response_model_not_flagged():
    rule = RawDictWithResponseModelRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/data")
def get_data():
    return {"key": "value"}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_dict_with_response_model_flagged():
    rule = RawDictWithResponseModelRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/user", response_model=UserSchema)
def get_user():
    return {"name": "test", "age": 25}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT043"
    assert diagnostics[0].severity == Severity.ERROR


def test_bad_list_with_response_model_flagged():
    rule = RawDictWithResponseModelRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/users", response_model=list[UserSchema])
def get_users():
    return [{"name": "a"}, {"name": "b"}]
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
