import ast

from fastapi_doctor.rules.architecture.fastt027_file_instead_of_uploadfile import (
    FileInsteadOfUploadFileRule,
)
from fastapi_doctor.models import Severity


def test_good_uploadfile_not_flagged():
    rule = FileInsteadOfUploadFileRule()
    source = """
from fastapi import FastAPI, UploadFile
app = FastAPI()

@app.post("/upload")
async def upload(file: UploadFile):
    return {"filename": file.filename}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_non_file_param_not_flagged():
    rule = FileInsteadOfUploadFileRule()
    source = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"id": item_id}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_bytes_file_flagged():
    rule = FileInsteadOfUploadFileRule()
    source = """
from fastapi import FastAPI, File
app = FastAPI()

@app.post("/upload")
async def upload(file: bytes = File()):
    return {"size": len(file)}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT027"
    assert diagnostics[0].severity == Severity.WARNING


def test_bad_multiple_bytes_params_flagged():
    rule = FileInsteadOfUploadFileRule()
    source = """
from fastapi import FastAPI, File
app = FastAPI()

@app.post("/upload")
async def upload(file: bytes = File(), thumb: bytes = File(default=None)):
    return {"size": len(file)}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 2


def test_sync_endpoint_also_flagged():
    rule = FileInsteadOfUploadFileRule()
    source = """
from fastapi import FastAPI, File
app = FastAPI()

@app.post("/upload")
def upload(file: bytes = File()):
    return {"size": len(file)}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
