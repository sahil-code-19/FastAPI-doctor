import ast

from fastapi_doctor.rules.dependency.fastt053_route_level_auth import (
    RouteLevelAuthRule,
)
from fastapi_doctor.models import Severity


def test_good_router_level_auth_not_flagged():
    rule = RouteLevelAuthRule()
    source = """
from fastapi import APIRouter, Depends
from app.auth import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.get("/me")
def get_me():
    return {}

@router.get("/settings")
def get_settings():
    return {}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_good_no_auth_not_flagged():
    rule = RouteLevelAuthRule()
    source = """
from fastapi import APIRouter

router = APIRouter()

@router.get("/public")
def public():
    return {}

@router.post("/data")
def create_data():
    return {}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0


def test_bad_route_level_auth_flagged():
    rule = RouteLevelAuthRule()
    source = """
from fastapi import APIRouter, Depends
from app.auth import get_current_user

router = APIRouter()

@router.get("/me")
def get_me(user = Depends(get_current_user)):
    return {"user": user}

@router.get("/settings")
def get_settings():
    return {}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1
    assert diagnostics[0].rule == "fastapi-doctor/FASTT053"
    assert diagnostics[0].severity == Severity.WARNING


def test_bad_route_level_auth_in_deps_flagged():
    rule = RouteLevelAuthRule()
    source = """
from fastapi import APIRouter, Depends
from app.auth import get_current_user

router = APIRouter()

@router.get("/me", dependencies=[Depends(get_current_user)])
def get_me():
    return {}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 1


def test_good_router_auth_covers_all():
    rule = RouteLevelAuthRule()
    source = """
from fastapi import APIRouter, Depends
from app.auth import get_current_user, verify_token

router = APIRouter(dependencies=[Depends(get_current_user), Depends(verify_token)])

@router.get("/me")
def get_me(user = Depends(get_current_user)):
    return {"user": user}

@router.get("/admin")
def admin(user = Depends(verify_token)):
    return {}
"""
    tree = ast.parse(source)
    diagnostics = rule.check(tree, "test.py", source)
    assert len(diagnostics) == 0