import ast
from pathlib import Path

from fastapi_doctor.rules.async_sync.fastt004_nested_event_loop import (
    NestedEventLoopRule,
)
from fastapi_doctor.models import Severity

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "fastt004"


def test_good_no_diagnostics():
    rule = NestedEventLoopRule()
    source = (FIXTURES / "good.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "good.py", source)
    assert len(diagnostics) == 0, (
        f"Expected 0 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )


def test_bad_detects_nested_event_loop():
    rule = NestedEventLoopRule()
    source = (FIXTURES / "bad.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "bad.py", source)

    assert len(diagnostics) == 3, (
        f"Expected 2 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )

    for diag in diagnostics:
        assert diag.rule == "fastapi-doctor/FASTT004"
        assert diag.severity == Severity.ERROR


def test_sync_endpoint_not_flagged():
    rule = NestedEventLoopRule()
    source = """
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/items")
def get_items():
    asyncio.run(something())
    return {"items": []}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Sync endpoints should not be flagged"


def test_non_endpoint_async_not_flagged():
    rule = NestedEventLoopRule()
    source = """
import asyncio

async def helper():
    asyncio.run(something())
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Non-endpoint async functions should not be flagged"


def test_asyncio_run_inside_to_thread_not_flagged():
    rule = NestedEventLoopRule()
    source = """
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/items")
async def get_items():
    def sync_work():
        asyncio.run(inner_sync())
    await asyncio.to_thread(sync_work)
    return {}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "asyncio.run inside to_thread should not be flagged"


def test_asyncio_run_inside_inner_function_not_flagged():
    rule = NestedEventLoopRule()
    source = """
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/items")
async def get_items():
    def inner():
        asyncio.run(something())
    inner()
    return {}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, (
        "asyncio.run inside inner sync function should not be flagged"
    )


def test_asyncio_run_inside_async_inner_function_flagged():
    rule = NestedEventLoopRule()
    source = """
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.put("/items/{id}")
async def update_item(id: int):
    async def helper():
        asyncio.run(something())
    await helper()
    return {"status": "updated"}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1, (
        f"asyncio.run inside inner async function should be flagged, "
        f"got {[(d.message, d.line) for d in diagnostics]}"
    )


def test_check_function_flags_crud():
    rule = NestedEventLoopRule()
    source = """
import asyncio

async def create_user():
    asyncio.run(db_insert())
    return {"status": "created"}
"""
    tree = ast.parse(source)
    func_node = tree.body[1]
    diagnostics = rule.check_function(func_node, "test.py")
    assert len(diagnostics) == 1, "CRUD function with asyncio.run should be flagged"


def test_check_function_skips_sync():
    rule = NestedEventLoopRule()
    source = "def helper(): asyncio.run(something())"
    tree = ast.parse(source)
    func_node = tree.body[0]
    diagnostics = rule.check_function(func_node, "test.py")
    assert len(diagnostics) == 0, "Sync functions should not be flagged"
