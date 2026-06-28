import ast

from fastapi_doctor.rules.architecture.fastt021_global_mutable_state import (
    GlobalMutableStateRule,
)
from fastapi_doctor.models import Severity


def test_good_local_state_not_flagged():
    rule = GlobalMutableStateRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/count")
def get_count():
    counter = 0
    counter += 1
    return {"count": counter}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_global_read_not_flagged():
    rule = GlobalMutableStateRule()
    source = """
from fastapi import FastAPI
app = FastAPI()
SETTINGS = {"debug": True}

@app.get("/settings")
def get_settings():
    return {"debug": SETTINGS["debug"]}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_global_augassign_flagged():
    rule = GlobalMutableStateRule()
    source = """
from fastapi import FastAPI
app = FastAPI()
request_count = 0

@app.get("/increment")
def increment():
    global request_count
    request_count += 1
    return {"count": request_count}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) >= 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT021"
    assert diagnostics[0].severity == Severity.WARNING


def test_bad_global_append_flagged():
    rule = GlobalMutableStateRule()
    source = """
from fastapi import FastAPI
app = FastAPI()
log_entries = []

@app.post("/log")
def add_log():
    global log_entries
    log_entries.append("new entry")
    return {"ok": True}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) >= 1


def test_good_no_global_not_flagged():
    rule = GlobalMutableStateRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/ping")
def ping():
    return {"status": "ok"}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_dict_mutation_without_global_flagged():
    """Dict subscript mutation doesn't need 'global' keyword — should still be caught."""
    rule = GlobalMutableStateRule()
    source = """
from fastapi import FastAPI
app = FastAPI()
global_mut = {}

@app.get("/items")
async def update():
    global_mut["name"] = "sahil"
    return global_mut
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert "global_mut" in diagnostics[0].message


def test_list_append_without_global_flagged():
    """List append doesn't need 'global' keyword — should still be caught."""
    rule = GlobalMutableStateRule()
    source = """
from fastapi import FastAPI
app = FastAPI()
global_list = []

@app.get("/items")
def handler():
    global_list.append("koshti")
    return {}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert "global_list" in diagnostics[0].message


def test_set_add_without_global_flagged():
    rule = GlobalMutableStateRule()
    source = """
from fastapi import FastAPI
app = FastAPI()
seen = set()

@app.get("/track")
def track():
    seen.add("user_1")
    return {}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert "seen" in diagnostics[0].message
