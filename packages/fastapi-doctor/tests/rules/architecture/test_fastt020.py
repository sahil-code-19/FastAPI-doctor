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


def test_depends_in_non_endpoint_router_file_flagged():
    """Depends() inside a non-endpoint function but in a router file — should be flagged."""
    rule = DependsInBodyRule()
    source = """
from fastapi import FastAPI, Depends
app = FastAPI()

async def helper():
    db = Depends(get_db)
    return db

@app.get("/items")
async def get_items():
    return await helper()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert "helper" in diagnostics[0].message


def test_depends_in_non_router_file_skipped():
    """Depends() in a file with NO FastAPI endpoints — should NOT be flagged."""
    rule = DependsInBodyRule()
    source = """
from fastapi import Depends

async def helper():
    db = Depends(get_db)
    return db
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Non-router files should be skipped entirely"
