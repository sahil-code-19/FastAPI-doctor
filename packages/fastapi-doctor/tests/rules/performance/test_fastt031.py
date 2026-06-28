import ast

from fastapi_doctor.rules.performance.fastt031_unindexed_foreign_key import (
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


def test_sqlmodel_field_foreign_key_flagged():
    """SQLModel Field(foreign_key='...') without index should be flagged."""
    rule = UnindexedForeignKeyRule()
    source = """
from sqlmodel import SQLModel, Field

class Application(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="users.id")
    job_id: int = Field(foreign_key="jobs.id")
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 2
    assert "Field" in diagnostics[0].message


def test_sqlmodel_field_with_index_not_flagged():
    """SQLModel Field(foreign_key='...', index=True) should NOT be flagged."""
    rule = UnindexedForeignKeyRule()
    source = """
from sqlmodel import SQLModel, Field

class Application(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="users.id", index=True)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_mapped_column_unindexed_flagged():
    """SQLAlchemy 2.0 mapped_column(ForeignKey(...)) without index should be flagged."""
    rule = UnindexedForeignKeyRule()
    source = """
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import ForeignKey

class Post:
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert "mapped_column" in diagnostics[0].message


def test_mapped_column_with_index_not_flagged():
    """SA 2.0 mapped_column(ForeignKey(...), index=True) should NOT be flagged."""
    rule = UnindexedForeignKeyRule()
    source = """
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import ForeignKey

class Post:
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0
