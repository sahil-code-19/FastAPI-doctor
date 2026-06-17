import ast

from fastapi_doctor.rules.architecture.fastt022_god_file_pattern import (
    GodFilePatternRule,
)
from fastapi_doctor.models import Severity


def test_good_few_routes_not_flagged():
    rule = GodFilePatternRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def home():
    return {"hello": "world"}

@app.get("/users")
def get_users():
    return []
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_include_router_not_flagged():
    rule = GodFilePatternRule()
    source = """
from fastapi import FastAPI
from app.users import users_router
app = FastAPI()

@app.get("/")
def home():
    return {"hello": "world"}

@app.get("/users")
def get_users():
    return []

@app.post("/users")
def create_user():
    return {}

@app.get("/items")
def get_items():
    return []

@app.get("/health")
def health():
    return {}

app.include_router(users_router)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_god_file_flagged():
    rule = GodFilePatternRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def home():
    return {}

@app.get("/users")
def get_users():
    return []

@app.post("/users")
def create_user():
    return {}

@app.put("/users/{id}")
def update_user():
    return {}

@app.delete("/users/{id}")
def delete_user():
    return {}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) >= 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT022"
    assert diagnostics[0].severity == Severity.WARNING


def test_good_no_fastapi_not_flagged():
    rule = GodFilePatternRule()
    source = """
def greet():
    return "hello"

@app.get("/")
def home():
    return {}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0
