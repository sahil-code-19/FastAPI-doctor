import ast

from fastapi_doctor.rules.architecture.fastt024_raw_db_connect_startup import (
    RawDbConnectStartupRule,
)
from fastapi_doctor.models import Severity


def test_good_sqlalchemy_engine_not_flagged():
    rule = RawDbConnectStartupRule()
    source = """
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

app = FastAPI()
engine = create_async_engine("sqlite+aiosqlite:///db.sqlite3", pool_size=20)

@app.on_event("startup")
async def startup():
    pass
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_no_startup_not_flagged():
    rule = RawDbConnectStartupRule()
    source = """
import psycopg2

def run_migration():
    conn = psycopg2.connect("dbname=test")
    conn.close()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_psycopg2_connect_in_startup():
    rule = RawDbConnectStartupRule()
    source = """
from fastapi import FastAPI
import psycopg2
app = FastAPI()

@app.on_event("startup")
async def startup():
    conn = psycopg2.connect("dbname=test user=postgres")
    conn.close()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT024"
    assert diagnostics[0].severity == Severity.WARNING


def test_bad_sqlite3_connect_in_lifespan():
    rule = RawDbConnectStartupRule()
    source = """
from contextlib import asynccontextmanager
import sqlite3

@asynccontextmanager
async def lifespan(app):
    conn = sqlite3.connect("database.db")
    yield
    conn.close()
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) >= 1
