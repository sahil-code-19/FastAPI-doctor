import ast
from pathlib import Path

from fastapi_doctor.rules.security.fastt010_return_sqlalchemy_base_class import (
    ReturnSqlalchemyBaseClass,
)
from fastapi_doctor.models import Severity

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "fastt010"


def test_good_no_diagnostics():
    rule = ReturnSqlalchemyBaseClass()
    source = (FIXTURES / "good.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "good.py", source)
    assert len(diagnostics) == 0, (
        f"Expected 0 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )


def test_bad_detects_orm_return():
    rule = ReturnSqlalchemyBaseClass()
    source = (FIXTURES / "bad.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "bad.py", source)

    assert len(diagnostics) == 5, (
        f"Expected 6 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )

    for diag in diagnostics:
        assert diag.rule == "fastapi-doctor/FASTT010"
        assert diag.severity == Severity.ERROR


def test_variable_return_flagged():
    rule = ReturnSqlalchemyBaseClass()
    source = """
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

app = FastAPI()

@app.get("/users/{id}")
async def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    return user
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1, "Variable holding DB result should be flagged"


def test_sync_endpoint_also_checked():
    rule = ReturnSqlalchemyBaseClass()
    source = """
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

app = FastAPI()

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1, "Sync endpoints should also be checked"


def test_non_endpoint_not_flagged():
    rule = ReturnSqlalchemyBaseClass()
    source = """
async def helper(db):
    return db.query(User).first()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Non-endpoint functions should not be flagged"


def test_check_function_flags_crud():
    rule = ReturnSqlalchemyBaseClass()
    source = """
def get_user_by_id(db, user_id):
    return db.query(User).filter(User.id == user_id).first()
"""
    tree = ast.parse(source)
    func_node = tree.body[0]
    diagnostics = rule.check_function(func_node, "test.py")
    assert len(diagnostics) == 1, "CRUD function returning ORM model should be flagged"


def test_pydantic_schema_not_flagged():
    rule = ReturnSqlalchemyBaseClass()
    source = """
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

app = FastAPI()

class UserSchema(BaseModel):
    id: int
    name: str

@app.get("/users/{id}")
async def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(User).first()
    return UserSchema.model_validate(user)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Pydantic model_validate should not be flagged"
