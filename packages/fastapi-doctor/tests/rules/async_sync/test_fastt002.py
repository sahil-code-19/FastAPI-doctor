import ast
from pathlib import Path

from fastapi_doctor.rules.async_sync.fastt002_db_session_in_async import (
    DbSessionInAsyncRule,
)

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "fastt002"


def test_good_no_diagnostics():
    rule = DbSessionInAsyncRule()
    source = (FIXTURES / "good.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "good.py", source)
    assert len(diagnostics) == 0, (
        f"Expected 0 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )


def test_bad_detects_sync_db_calls():
    rule = DbSessionInAsyncRule()
    source = (FIXTURES / "bad.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "bad.py", source)

    assert len(diagnostics) == 8, (
        f"Expected 8 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )

    for diag in diagnostics:
        assert diag.rule == "fastapi-doctor/FASTT002"
        assert diag.severity.value == "error"


def test_non_endpoint_async_function_ignored():
    rule = DbSessionInAsyncRule()
    source = """
from sqlalchemy.orm import Session

async def helper():
    db = Session()
    db.execute("SELECT 1")
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Non-endpoint async functions should not be checked"


def test_sync_endpoint_not_flagged():
    rule = DbSessionInAsyncRule()
    source = """
from fastapi import FastAPI
from sqlalchemy.orm import Session

app = FastAPI()

@app.get("/users")
def get_users():
    db = Session()
    db.execute("SELECT * FROM users")
    return []
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Sync endpoints should not be flagged"


def test_async_session_not_flagged():
    rule = DbSessionInAsyncRule()
    source = """
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

@app.get("/users")
async def get_users(async_db: AsyncSession = Depends(get_async_db)):
    result = await async_db.execute("SELECT * FROM users")
    return []
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "AsyncSession should not be flagged"


def test_wrapped_in_to_thread_not_flagged():
    rule = DbSessionInAsyncRule()
    source = """
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/users")
async def get_users():
    def sync_work():
        db = get_db()
        db.execute("SELECT 1")
    await asyncio.to_thread(sync_work)
    return []
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, (
        "DB call inside asyncio.to_thread() should not be flagged"
    )
