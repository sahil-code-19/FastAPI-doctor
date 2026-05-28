import ast
from pathlib import Path

from fastapi_doctor.rules.async_sync.fastt005_blocking_file_io import (
    BlockingFileIORule,
)
from fastapi_doctor.models import Severity

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "fastt005"


def test_good_no_diagnostics():
    rule = BlockingFileIORule()
    source = (FIXTURES / "good.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "good.py", source)
    assert len(diagnostics) == 0, (
        f"Expected 0 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )


def test_bad_detects_blocking_open():
    rule = BlockingFileIORule()
    source = (FIXTURES / "bad.py").read_text()
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "bad.py", source)

    assert len(diagnostics) == 3, (
        f"Expected 3 violations, got {len(diagnostics)}: "
        f"{[(d.message, d.line) for d in diagnostics]}"
    )

    for diag in diagnostics:
        assert diag.rule == "fastapi-doctor/FASTT005"
        assert diag.severity == Severity.ERROR


def test_sync_endpoint_not_flagged():
    rule = BlockingFileIORule()
    source = """
from fastapi import FastAPI

app = FastAPI()

@app.get("/items")
def get_items():
    with open("data.txt") as f:
        return f.read()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Sync endpoints should not be flagged"


def test_non_endpoint_async_not_flagged():
    rule = BlockingFileIORule()
    source = """
async def helper():
    with open("data.txt") as f:
        return f.read()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "Non-endpoint async functions should not be flagged"


def test_open_inside_to_thread_not_flagged():
    rule = BlockingFileIORule()
    source = """
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/items")
async def get_items():
    def read_file():
        with open("data.txt") as f:
            return f.read()
    return await asyncio.to_thread(read_file)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0, "open() inside to_thread should not be flagged"


def test_check_function_flags_crud():
    rule = BlockingFileIORule()
    source = """
async def load_config():
    with open("config.json") as f:
        return f.read()
"""
    tree = ast.parse(source)
    func_node = tree.body[0]
    diagnostics = rule.check_function(func_node, "test.py")
    assert len(diagnostics) == 1, "CRUD function with open() should be flagged"


def test_check_function_skips_sync():
    rule = BlockingFileIORule()
    source = "def helper(): open('data.txt')"
    tree = ast.parse(source)
    func_node = tree.body[0]
    diagnostics = rule.check_function(func_node, "test.py")
    assert len(diagnostics) == 0, "Sync functions should not be flagged"
