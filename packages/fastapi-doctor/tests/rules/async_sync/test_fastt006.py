import ast
from pathlib import Path

from fastapi_doctor.rules.async_sync.fastt006_sync_subprocess import (
    SyncSubprocessRule,
)
from fastapi_doctor.models import Severity

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "fastt006"


def test_good_no_diagnostics():
    rule = SyncSubprocessRule()
    source = (FIXTURES / "good.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "good.py", source)
    assert len(diagnostics) == 0, (
        f"Expected 0 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )


def test_bad_detects_blocking_subprocess():
    rule = SyncSubprocessRule()
    source = (FIXTURES / "bad.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "bad.py", source)

    assert len(diagnostics) == 4, (
        f"Expected 4 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )

    for diag in diagnostics:
        assert diag.rule == "fastapi-doctor/FASTT006"
        assert diag.severity == Severity.WARNING


def test_sync_endpoint_not_flagged():
    rule = SyncSubprocessRule()
    source = """
from fastapi import FastAPI
import subprocess

app = FastAPI()

@app.get("/items")
def get_items():
    subprocess.run(["ls"])
    return {"items": []}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Sync endpoints should not be flagged"


def test_non_endpoint_async_not_flagged():
    rule = SyncSubprocessRule()
    source = """
import subprocess

async def helper():
    subprocess.run(["ls"])
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Non-endpoint async functions should not be flagged"


def test_subprocess_inside_to_thread_not_flagged():
    rule = SyncSubprocessRule()
    source = """
from fastapi import FastAPI
import asyncio
import subprocess

app = FastAPI()

@app.get("/items")
async def get_items():
    def run_cmd():
        subprocess.run(["echo", "hello"])
    return await asyncio.to_thread(run_cmd)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "subprocess inside to_thread should not be flagged"


def test_check_function_flags_crud():
    rule = SyncSubprocessRule()
    source = """
import subprocess

async def run_health_check():
    result = subprocess.run(["uptime"], capture_output=True)
    return result.stdout
"""
    tree = ast.parse(source)
    func_node = tree.body[1]
    diagnostics = rule.check_function(func_node, "test.py")
    assert len(diagnostics) == 1, "CRUD function with subprocess.run should be flagged"


def test_check_function_skips_sync():
    rule = SyncSubprocessRule()
    source = "def helper(): subprocess.run(['ls'])"
    tree = ast.parse(source)
    func_node = tree.body[0]
    diagnostics = rule.check_function(func_node, "test.py")
    assert len(diagnostics) == 0, "Sync functions should not be flagged"
