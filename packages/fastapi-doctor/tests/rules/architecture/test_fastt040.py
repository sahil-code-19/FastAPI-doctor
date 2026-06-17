import ast

from fastapi_doctor.rules.architecture.fastt040_pydantic_v1_validator import (
    PydanticV1ValidatorRule,
)
from fastapi_doctor.models import Severity


def test_good_field_validator_not_flagged():
    rule = PydanticV1ValidatorRule()
    source = """
from pydantic import BaseModel, field_validator

class UserModel(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        return v
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_no_validators_not_flagged():
    rule = PydanticV1ValidatorRule()
    source = """
from pydantic import BaseModel

class ItemModel(BaseModel):
    name: str
    price: float
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_v1_validator_flagged():
    rule = PydanticV1ValidatorRule()
    source = """
from pydantic import BaseModel, validator

class UserModel(BaseModel):
    name: str

    @validator("name")
    def validate_name(cls, v):
        return v
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT040"
    assert diagnostics[0].severity == Severity.WARNING


def test_bad_multiple_v1_validators_flagged():
    rule = PydanticV1ValidatorRule()
    source = """
from pydantic import BaseModel, validator

class UserModel(BaseModel):
    name: str
    age: int

    @validator("name")
    def validate_name(cls, v):
        return v

    @validator("age")
    def validate_age(cls, v):
        return v
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 2
