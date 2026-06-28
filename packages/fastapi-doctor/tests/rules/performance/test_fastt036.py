import ast

from fastapi_doctor.rules.performance.fastt036_missing_lru_cache import (
    MissingLruCacheRule,
)
from fastapi_doctor.models import Severity


def test_good_lru_cache_decorated_not_flagged():
    rule = MissingLruCacheRule()
    source = """
from functools import lru_cache

@lru_cache
def get_settings():
    return {"debug": True}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "config.py", source)
    assert len(diagnostics) == 0


def test_good_cache_decorated_not_flagged():
    rule = MissingLruCacheRule()
    source = """
from functools import cache

@cache
def get_config():
    return {"host": "localhost"}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "config.py", source)
    assert len(diagnostics) == 0


def test_good_non_settings_func_not_flagged():
    rule = MissingLruCacheRule()
    source = """
def load_data():
    return [1, 2, 3]
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "config.py", source)
    assert len(diagnostics) == 0


def test_bad_missing_lru_cache_flagged():
    rule = MissingLruCacheRule()
    source = """
def get_settings():
    import os
    return {"secret_key": os.environ["SECRET_KEY"]}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "config.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT036"
    assert diagnostics[0].severity == Severity.WARNING


def test_bad_missing_cache_on_load_settings_flagged():
    rule = MissingLruCacheRule()
    source = """
def load_settings():
    return {"env": "production"}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "config.py", source)
    assert len(diagnostics) == 1
