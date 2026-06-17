import ast

from fastapi_doctor.rules.architecture.fastt041_orm_mode_unused import (
    OrmModeUnusedRule,
)
from fastapi_doctor.models import Severity


def test_good_no_orm_mode_not_flagged():
    rule = OrmModeUnusedRule()
    source = """
from pydantic import BaseModel

class UserSchema(BaseModel):
    id: int
    name: str
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_orm_mode_with_from_orm_not_flagged():
    rule = OrmModeUnusedRule()
    source = """
from pydantic import BaseModel

class UserSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

def get_users():
    users = db.query(User).all()
    return [UserSchema.from_orm(u) for u in users]
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_orm_mode_no_from_orm_flagged():
    rule = OrmModeUnusedRule()
    source = """
from pydantic import BaseModel

class UserSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT041"
    assert diagnostics[0].severity == Severity.WARNING


def test_good_not_basemodel_not_flagged():
    rule = OrmModeUnusedRule()
    source = """
class PlainClass:
    class Config:
        orm_mode = True
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0
