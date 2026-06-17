import ast

from fastapi_doctor.rules.architecture.fastt034_background_tasks_celery import (
    BackgroundTasksCeleryRule,
)
from fastapi_doctor.models import Severity


def test_good_no_celery_import_not_flagged():
    rule = BackgroundTasksCeleryRule()
    source = """
from fastapi import FastAPI, BackgroundTasks
app = FastAPI()

@app.post("/send")
def send_email(bg: BackgroundTasks):
    bg.add_task(send_email_task, "hello@example.com")
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_celery_but_no_bg_not_flagged():
    rule = BackgroundTasksCeleryRule()
    source = """
from celery import Celery
from fastapi import FastAPI
app = FastAPI()
celery_app = Celery()

@app.post("/task")
def run_task():
    long_task.delay()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_celery_with_backgroundtasks_flagged():
    rule = BackgroundTasksCeleryRule()
    source = """
from celery import Celery
from fastapi import FastAPI, BackgroundTasks
app = FastAPI()
celery_app = Celery()

@app.post("/task")
def run_task(bg: BackgroundTasks):
    bg.add_task(long_task.delay)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT034"
    assert diagnostics[0].severity == Severity.WARNING


def test_bad_celery_importfrom_flagged():
    rule = BackgroundTasksCeleryRule()
    source = """
from myapp.celery_app import celery
from fastapi import FastAPI, BackgroundTasks
app = FastAPI()

@app.post("/email")
async def send_email(bg: BackgroundTasks):
    bg.add_task(send_celery_email)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) >= 1
