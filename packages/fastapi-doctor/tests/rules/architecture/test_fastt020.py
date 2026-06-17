import ast

from fastapi_doctor.rules.architecture.fastt020_depends_in_body import (
    DependsInBodyRule,
)
from fastapi_doctor.models import Severity


def test_good_depends_as_parameter_not_flagged():
    rule = DependsInBodyRule()
    source = """
from fastapi import FastAPI, Depends
app = FastAPI()

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_no_depends_not_flagged():
    rule = DependsInBodyRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def home():
    return {"hello": "world"}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_depends_in_body_flagged():
    rule = DependsInBodyRule()
    source = """
from fastapi import FastAPI, Depends
app = FastAPI()

@app.get("/users")
def get_users():
    db = Depends(get_db)
    return db.query(User).all()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT020"
    assert diagnostics[0].severity == Severity.ERROR


def test_bad_depends_in_async_body_flagged():
    rule = DependsInBodyRule()
    source = """
from fastapi import FastAPI, Depends
app = FastAPI()

@app.get("/users")
async def get_users():
    db = Depends(get_db)
    return await db.query(User).all()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
