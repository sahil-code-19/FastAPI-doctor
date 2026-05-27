import ast
from pathlib import Path

from fastapi_doctor.rules.async_sync.fastt001_sync_blocking_io import SyncBlockingIORule

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "fastt001"


def test_good_async_no_diagnostics():
    rule = SyncBlockingIORule()
    source = (FIXTURES / "good.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "good.py", source)
    assert len(diagnostics) == 0, (
        f"Expected 0 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )


def test_bad_async_detects_blocking_calls():
    rule = SyncBlockingIORule()
    source = (FIXTURES / "bad.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "bad.py", source)

    assert len(diagnostics) == 5, (
        f"Expected 5 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )

    for diag in diagnostics:
        assert diag.rule == "fastapi-doctor/FASTT001"
        assert diag.severity.value == "error"


def test_non_endpoint_async_function_ignored():
    rule = SyncBlockingIORule()
    source = """
import requests

async def helper():
    response = requests.get("https://example.com")
    return response.json()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Non-endpoint async functions should not be checked"


def test_blocking_in_sync_endpoint_not_flagged():
    rule = SyncBlockingIORule()
    source = """
from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/users")
def get_users():
    return requests.get("https://example.com/users").json()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Sync endpoints should not be flagged for blocking IO"


def test_blocking_in_to_thread_not_flagged():
    rule = SyncBlockingIORule()
    source = """
from fastapi import FastAPI
import asyncio
import requests

app = FastAPI()

@app.get("/users")
async def get_users():
    response = await asyncio.to_thread(requests.get, "https://example.com/users")
    return response.json()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, (
        "Blocking call inside asyncio.to_thread() should not be flagged"
    )


def test_blocking_in_run_in_threadpool_not_flagged():
    rule = SyncBlockingIORule()
    source = """
from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
import requests

app = FastAPI()

@app.get("/users")
async def get_users():
    response = await run_in_threadpool(requests.get, "https://example.com/users")
    return response.json()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, (
        "Blocking call inside run_in_threadpool() should not be flagged"
    )
