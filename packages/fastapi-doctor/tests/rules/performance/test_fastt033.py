import ast

from fastapi_doctor.rules.performance.fastt033_cpu_bound_in_async import (
    CpuBoundInAsyncRule,
)
from fastapi_doctor.models import Severity


def test_good_sync_endpoint_not_flagged():
    rule = CpuBoundInAsyncRule()
    source = """
from fastapi import FastAPI
import cv2
app = FastAPI()

@app.post("/process")
def process_image():
    img = cv2.imread("file.jpg")
    return {}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_cpu_bound_wrapped_in_to_thread():
    rule = CpuBoundInAsyncRule()
    source = """
from fastapi import FastAPI
import asyncio
app = FastAPI()

@app.post("/process")
async def process_image():
    img = await asyncio.to_thread(cv2.imread, "file.jpg")
    return {}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_pil_image_open_in_async():
    rule = CpuBoundInAsyncRule()
    source = """
from fastapi import FastAPI
from PIL import Image
app = FastAPI()

@app.post("/thumbnail")
async def create_thumbnail():
    img = Image.open("file.jpg")
    return {}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT033"
    assert diagnostics[0].severity == Severity.WARNING


def test_bad_cv2_imread_in_async():
    rule = CpuBoundInAsyncRule()
    source = """
from fastapi import FastAPI
import cv2
app = FastAPI()

@app.post("/process")
async def process():
    img = cv2.imread("file.jpg")
    return {}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1


def test_bad_pil_image_direct_import():
    rule = CpuBoundInAsyncRule()
    source = """
from fastapi import FastAPI
import PIL.Image
app = FastAPI()

@app.post("/thumb")
async def thumb():
    img = PIL.Image.open("file.jpg")
    return {}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
