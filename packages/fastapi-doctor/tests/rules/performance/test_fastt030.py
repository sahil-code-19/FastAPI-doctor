import ast

from fastapi_doctor.rules.performance.fastt030_n_plus_one_query import (
    NPlusOneQueryRule,
)
from fastapi_doctor.models import Severity


def test_good_single_query_not_flagged():
    rule = NPlusOneQueryRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_loop_without_db_call_not_flagged():
    rule = NPlusOneQueryRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/process")
def process():
    for i in range(10):
        x = i * 2
    return {"ok": True}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_n_plus_one_flagged():
    rule = NPlusOneQueryRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/users-with-posts")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    for user in users:
        posts = db.query(Post).all()
    return users
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT030"
    assert diagnostics[0].severity == Severity.ERROR


def test_bad_db_get_in_loop_flagged():
    rule = NPlusOneQueryRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/items")
def get_items(db: Session = Depends(get_db)):
    ids = [1, 2, 3]
    result = []
    for item_id in ids:
        item = db.get(Item, item_id)
        result.append(item)
    return result
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
