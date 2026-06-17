import ast

from fastapi_doctor.rules.architecture.fastt044_missing_from_attributes import (
    MissingFromAttributesRule,
)
from fastapi_doctor.models import Severity


def test_good_with_configdict_not_flagged():
    rule = MissingFromAttributesRule()
    source = """
from pydantic import BaseModel, ConfigDict

class UserSchema(BaseModel):
    id: int
    name: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_with_orm_mode_not_flagged():
    rule = MissingFromAttributesRule()
    source = """
from pydantic import BaseModel

class UserSchema(BaseModel):
    id: int
    name: str
    created_at: str

    class Config:
        orm_mode = True
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_no_db_fields_not_flagged():
    rule = MissingFromAttributesRule()
    source = """
from pydantic import BaseModel

class LoginSchema(BaseModel):
    username: str
    password: str
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_missing_from_attributes_flagged():
    rule = MissingFromAttributesRule()
    source = """
from pydantic import BaseModel

class UserSchema(BaseModel):
    id: int
    name: str
    created_at: str
    updated_at: str
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT044"
    assert diagnostics[0].severity == Severity.WARNING


def test_bad_missing_one_db_field_not_enough():
    rule = MissingFromAttributesRule()
    source = """
from pydantic import BaseModel

class UserSchema(BaseModel):
    id: int
    name: str
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0
