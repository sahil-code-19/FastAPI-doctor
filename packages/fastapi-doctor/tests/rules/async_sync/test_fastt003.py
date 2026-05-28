import ast
from pathlib import Path

from fastapi_doctor.rules.async_sync.fastt003_no_await_in_async import (
    NoAwaitInAsyncRule,
)
from fastapi_doctor.models import Severity

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "fastt003"


def test_good_no_diagnostics():
    rule = NoAwaitInAsyncRule()
    source = (FIXTURES / "good.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "good.py", source)
    assert len(diagnostics) == 0, (
        f"Expected 0 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )


def test_bad_detects_no_await_error():
    rule = NoAwaitInAsyncRule()
    source = (FIXTURES / "bad.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "bad.py", source)

    assert len(diagnostics) == 3, (
        f"Expected 3 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )

    for diag in diagnostics:
        assert diag.rule == "fastapi-doctor/FASTT003"
        assert diag.severity == Severity.ERROR


def test_sync_endpoint_not_flagged():
    rule = NoAwaitInAsyncRule()
    source = """
from fastapi import FastAPI

app = FastAPI()

@app.get("/items")
def get_items():
    return {"items": []}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Sync endpoints should not be flagged"


def test_non_endpoint_async_not_flagged():
    rule = NoAwaitInAsyncRule()
    source = """
async def helper():
    return 42
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Non-endpoint async functions should not be checked"


def test_async_with_counts_as_async():
    rule = NoAwaitInAsyncRule()
    source = """
from fastapi import FastAPI

app = FastAPI()

@app.get("/items")
async def get_items():
    async with get_session() as session:
        return session.data
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "async with should count as async construct"


def test_async_for_counts_as_async():
    rule = NoAwaitInAsyncRule()
    source = """
from fastapi import FastAPI

app = FastAPI()

@app.get("/items")
async def stream_items():
    results = []
    async for item in stream():
        results.append(item)
    return results
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "async for should count as async construct"


def test_inner_async_does_not_satisfy_outer():
    rule = NoAwaitInAsyncRule()
    source = """
from fastapi import FastAPI

app = FastAPI()

@app.get("/items")
async def get_items():
    async def inner():
        await something()
    return []
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1, (
        "Inner async function's await should not satisfy outer endpoint"
    )


def test_check_function_respects_sync():
    rule = NoAwaitInAsyncRule()
    source = "def helper(): return 1"
    tree = ast.parse(source)
    func_node = tree.body[0]
    diagnostics = rule.check_function(func_node, "test.py")
    assert len(diagnostics) == 0, (
        "Sync functions should not be flagged by check_function"
    )


def test_check_function_flags_async_no_await():
    rule = NoAwaitInAsyncRule()
    source = "async def helper(): return 1"
    tree = ast.parse(source)
    func_node = tree.body[0]
    diagnostics = rule.check_function(func_node, "test.py")
    assert len(diagnostics) == 1, "Async CRUD function with no await should be flagged"


def test_async_param_gives_warning_not_error():
    rule = NoAwaitInAsyncRule()
    source = """
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

@app.post("/refresh")
async def refresh(data: dict, db: AsyncSession = Depends(get_async_db)):
    user = get_current_user(data)
    return {"token": create_token(user)}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.WARNING, (
        f"Expected WARNING for async-capable param, got {diagnostics[0].severity}"
    )


def test_no_async_param_gives_error():
    rule = NoAwaitInAsyncRule()
    source = """
from fastapi import FastAPI

app = FastAPI()

@app.get("/items")
async def get_items():
    return {"items": []}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR, (
        f"Expected ERROR for no async params, got {diagnostics[0].severity}"
    )


def test_depends_async_dependency_gives_warning():
    rule = NoAwaitInAsyncRule()
    source = """
from fastapi import FastAPI, Depends

app = FastAPI()

@app.get("/items")
async def get_items(db = Depends(get_async_session)):
    return {"items": []}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.WARNING, (
        f"Expected WARNING for Depends(async_dep), got {diagnostics[0].severity}"
    )


def test_regular_depends_still_error():
    rule = NoAwaitInAsyncRule()
    source = """
from fastapi import FastAPI, Depends

app = FastAPI()

@app.get("/items")
async def get_items(db = Depends(get_db)):
    return {"items": []}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR, (
        f"Expected ERROR for non-async Depends, got {diagnostics[0].severity}"
    )
