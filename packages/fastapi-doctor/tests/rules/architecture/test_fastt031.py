import ast

from fastapi_doctor.rules.architecture.fastt031_unindexed_foreign_key import (
    UnindexedForeignKeyRule,
)
from fastapi_doctor.models import Severity


def test_good_foreignkey_with_index_not_flagged():
    rule = UnindexedForeignKeyRule()
    source = """
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey("users.id"), index=True)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_no_foreignkey_not_flagged():
    rule = UnindexedForeignKeyRule()
    source = """
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String(100))
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_unindexed_foreignkey_flagged():
    rule = UnindexedForeignKeyRule()
    source = """
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey("users.id"))
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT031"
    assert diagnostics[0].severity == Severity.WARNING


def test_bad_unindexed_foreignkey_with_other_kw_flagged():
    rule = UnindexedForeignKeyRule()
    source = """
from sqlalchemy import Column, Integer, ForeignKey
Base = None

class Post:
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
