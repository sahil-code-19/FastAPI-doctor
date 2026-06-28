import ast

from fastapi_doctor.rules.dependency.fastt051_repeated_depends import (
    RepeatedDependsRule,
)
from fastapi_doctor.models import Severity


def test_good_few_depends_not_flagged():
    rule = RepeatedDependsRule()
    source = """
from fastapi import FastAPI, Depends
from app.database import get_db
app = FastAPI()

@app.get("/users")
def get_users(db = Depends(get_db)):
    return []

@app.post("/users")
def create_user(db = Depends(get_db)):
    return {}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_no_depends_not_flagged():
    rule = RepeatedDependsRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/users")
def get_users():
    return []

@app.get("/items")
def get_items():
    return []
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_repeated_depends_flagged():
    rule = RepeatedDependsRule()
    source = """
from fastapi import FastAPI, Depends
from app.database import get_db
app = FastAPI()

@app.get("/users", dependencies=[Depends(get_db)])
def get_users():
    return []

@app.post("/users", dependencies=[Depends(get_db)])
def create_user():
    return {}

@app.put("/users/1", dependencies=[Depends(get_db)])
def update_user():
    return {}

@app.delete("/users/1", dependencies=[Depends(get_db)])
def delete_user():
    return {}

@app.get("/items", dependencies=[Depends(get_db)])
def get_items():
    return []
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT051"
    assert diagnostics[0].severity == Severity.WARNING


def test_bad_repeated_depends_as_param_flagged():
    rule = RepeatedDependsRule()
    source = """
from fastapi import FastAPI, Depends
from app.database import get_db
app = FastAPI()

@app.get("/a")
def get_a(db = Depends(get_db)):
    return []

@app.get("/b")
def get_b(db = Depends(get_db)):
    return []

@app.get("/c")
def get_c(db = Depends(get_db)):
    return []

@app.get("/d")
def get_d(db = Depends(get_db)):
    return []

@app.get("/e")
def get_e(db = Depends(get_db)):
    return []
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
