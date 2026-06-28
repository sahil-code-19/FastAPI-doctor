import ast

from fastapi_doctor.rules.performance.fastt032_missing_joinedload import (
    MissingJoinedloadRule,
)
from fastapi_doctor.models import Severity


def test_related_models_flagged():
    """order = db.get(Order, 1) then user = db.get(User, order.user_id) → flagged."""
    rule = MissingJoinedloadRule()
    source = """
from fastapi import FastAPI, Depends
app = FastAPI()

class Order:
    user_id = Column(Integer, ForeignKey("users.id"))

@app.get("/orders/{id}")
async def get_order(id: int, db = Depends(get_db)):
    order = db.get(Order, id)
    user = db.get(User, order.user_id)
    return order
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) >= 1
    assert "joinedload" in diagnostics[0].help or "User" in diagnostics[0].message


def test_unrelated_queries_not_flagged():
    """Two db.get() for unrelated models → not flagged."""
    rule = MissingJoinedloadRule()
    source = """
from fastapi import FastAPI, Depends
app = FastAPI()

@app.get("/data")
async def get_data(db = Depends(get_db)):
    order = db.get(Order, 1)
    stats = db.get(Stats, 99)
    return {"order": order, "stats": stats}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_same_model_not_flagged():
    """Two db.get() for same model, different IDs → not flagged."""
    rule = MissingJoinedloadRule()
    source = """
from fastapi import FastAPI, Depends
app = FastAPI()

@app.get("/orders/{id}")
async def get_orders(id: int, db = Depends(get_db)):
    order1 = db.get(Order, id)
    order2 = db.get(Order, id + 1)
    return [order1, order2]
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_sqlmodel_field_fk_pattern():
    """SQLModel Field(foreign_key='...') pattern — verification should work."""
    rule = MissingJoinedloadRule()
    source = """
from fastapi import FastAPI, Depends
app = FastAPI()

class Application:
    candidate_id: int = Field(foreign_key="users.id")

@app.get("/apps/{id}")
async def get_app(id: int, db = Depends(get_db)):
    app = db.get(Application, id)
    user = db.get(User, app.candidate_id)
    return app
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) >= 1


def test_select_pattern_detected():
    """db.execute(select(User)) pattern — model extracted from select()."""
    rule = MissingJoinedloadRule()
    source = """
from fastapi import FastAPI, Depends
from sqlalchemy import select
app = FastAPI()

class Order:
    user_id = Column(Integer, ForeignKey("users.id"))

@app.get("/orders")
async def get_orders(db = Depends(get_db)):
    orders = db.execute(select(Order))
    users = db.execute(select(User))
    return orders
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Different models via select, not accessing FK"


def test_variable_in_non_db_context_not_flagged():
    """order.user_id used in print, not DB call → not flagged."""
    rule = MissingJoinedloadRule()
    source = """
from fastapi import FastAPI, Depends
app = FastAPI()

@app.get("/orders/{id}")
async def get_order(id: int, db = Depends(get_db)):
    order = db.get(Order, id)
    print(order.user_id)
    return order
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_joinedload_already_present():
    """If joinedload already in query, we don't re-flag."""
    rule = MissingJoinedloadRule()
    source = """
from fastapi import FastAPI, Depends
from sqlalchemy.orm import joinedload
app = FastAPI()

@app.get("/orders/{id}")
async def get_order(id: int, db = Depends(get_db)):
    order = db.execute(select(Order).options(joinedload(Order.user)))
    user = db.get(User, order.user_id)
    return order
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_sync_endpoint_also_checked():
    rule = MissingJoinedloadRule()
    source = """
from fastapi import FastAPI, Depends
app = FastAPI()

class Order:
    user_id = Column(Integer, ForeignKey("users.id"))

@app.get("/orders/{id}")
def get_order(id: int, db = Depends(get_db)):
    order = db.get(Order, id)
    user = db.get(User, order.user_id)
    return order
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) >= 1
