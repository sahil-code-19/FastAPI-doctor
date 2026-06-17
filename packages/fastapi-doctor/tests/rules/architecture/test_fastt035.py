import ast

from fastapi_doctor.rules.architecture.fastt035_unbounded_query import (
    UnboundedQueryRule,
)
from fastapi_doctor.models import Severity


def test_good_query_with_limit_not_flagged():
    rule = UnboundedQueryRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).limit(10).all()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_query_with_offset_not_flagged():
    rule = UnboundedQueryRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).offset(0).limit(10).all()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_unbounded_all_flagged():
    rule = UnboundedQueryRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT035"
    assert diagnostics[0].severity == Severity.ERROR


def test_bad_session_query_all_flagged():
    rule = UnboundedQueryRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/items")
def get_items(session: Session = Depends(get_db)):
    return session.query(Item).all()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1


def test_good_no_query_call_not_flagged():
    rule = UnboundedQueryRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def home():
    return {"message": "hello"}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0
