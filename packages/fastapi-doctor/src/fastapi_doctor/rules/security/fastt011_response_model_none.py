import ast

from fastapi_doctor.rules.base import Rule, register_rule, is_fastapi_endpoint
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity

SENSITIVE_KEYS = {
    "password",
    "hashed_password",
    "password_hash",
    "hash",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "secret",
    "private_key",
    "api_secret",
    "client_secret",
    "secret_key",
    "credential",
    "credentials",
    "session_id",
    "auth",
    "authorization",
}

ORM_METHODS = {"query", "execute", "get", "refresh"}
ORM_RESULT_METHODS = {
    "first",
    "all",
    "one",
    "get",
    "scalars",
    "fetchall",
    "fetchone",
    "scalar",
}


@register_rule
class ResponseModelNoneRule(Rule):
    """Detect response_model=None on routes returning sensitive data (FASTT011)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT011",
            severity=Severity.ERROR,
            description="response_model=None on a route returning sensitive data — bypasses Pydantic validation, leaking fields",
            recommendation="Define a Pydantic response model that includes only the fields you want to expose",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            method_name = is_fastapi_endpoint(node)
            if method_name is None:
                continue
            if not self._has_response_model_none(node):
                continue
            diagnostics.extend(self._check_single(node, file_path))
        return diagnostics

    def check_function(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: str
    ) -> list[Diagnostic]:
        return []

    def _has_response_model_none(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> bool:
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Call):
                for kw in decorator.keywords:
                    if kw.arg == "response_model" and isinstance(
                        kw.value, ast.Constant
                    ):
                        if kw.value.value is None:
                            return True
        return False

    def _check_single(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: str
    ) -> list[Diagnostic]:
        diagnostics = []

        inner_func_descendants = self._collect_inner_func_descendants(func_node)
        db_sourced_vars = self._collect_db_sourced_vars(
            func_node, inner_func_descendants
        )
        sensitive_vars = self._collect_sensitive_vars(func_node, inner_func_descendants)
        all_sensitive_vars = db_sourced_vars | sensitive_vars

        for node in ast.walk(func_node):
            if node in inner_func_descendants:
                continue
            if not isinstance(node, ast.Return):
                continue
            if node.value is None:
                continue

            if self._returns_sensitive_data(node.value, all_sensitive_vars):
                diagnostics.append(
                    Diagnostic(
                        severity=self.definition.severity,
                        file_path=file_path,
                        rule=self.definition.id,
                        message=f"endpoint '{func_node.name}' has response_model=None and returns sensitive data — validation bypassed",
                        line=node.lineno,
                        column=node.col_offset,
                        help=self.definition.recommendation,
                    )
                )

        return diagnostics

    def _returns_sensitive_data(
        self, value: ast.expr, sensitive_vars: set[str]
    ) -> bool:
        if isinstance(value, ast.Name) and value.id in sensitive_vars:
            return True
        if isinstance(value, ast.Call):
            if self._is_db_call(value):
                return True
            return False
        if isinstance(value, ast.Dict):
            for key in value.keys:
                if (
                    isinstance(key, ast.Constant)
                    and str(key.value).lower() in SENSITIVE_KEYS
                ):
                    return True
        return False

    def _is_db_call(self, call_node: ast.Call) -> bool:
        if not isinstance(call_node.func, ast.Attribute):
            return False
        attr = call_node.func.attr
        if attr in ORM_METHODS:
            return True
        if attr in ORM_RESULT_METHODS:
            return self._has_db_method_in_chain(call_node)
        return False

    def _has_db_method_in_chain(self, call_node: ast.Call) -> bool:
        if (
            isinstance(call_node.func, ast.Attribute)
            and call_node.func.attr in ORM_METHODS
        ):
            return True
        if isinstance(call_node.func, ast.Attribute):
            base = call_node.func.value
            if isinstance(base, ast.Call):
                return self._has_db_method_in_chain(base)
        return False

    def _collect_db_sourced_vars(
        self,
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
        inner_func_descendants: set[ast.AST],
    ) -> set[str]:
        db_sourced: set[str] = set()
        for node in ast.walk(func_node):
            if node in inner_func_descendants:
                continue
            if not isinstance(node, ast.Assign):
                continue
            if not self._expr_contains_db_call(node.value):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    db_sourced.add(target.id)
        return db_sourced

    def _expr_contains_db_call(self, expr: ast.expr) -> bool:
        for node in ast.walk(expr):
            if isinstance(node, ast.Call):
                if self._is_db_call(node):
                    return True
        return False

    def _collect_sensitive_vars(
        self,
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
        inner_func_descendants: set[ast.AST],
    ) -> set[str]:
        sensitive: set[str] = set()
        for node in ast.walk(func_node):
            if node in inner_func_descendants:
                continue
            if not isinstance(node, ast.Assign):
                continue
            if not self._is_sensitive_dict(node.value):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    sensitive.add(target.id)
        return sensitive

    def _is_sensitive_dict(self, expr: ast.expr) -> bool:
        if not isinstance(expr, ast.Dict):
            return False
        for key in expr.keys:
            if (
                isinstance(key, ast.Constant)
                and str(key.value).lower() in SENSITIVE_KEYS
            ):
                return True
        return False

    def _collect_inner_func_descendants(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> set[ast.AST]:
        descendants: set[ast.AST] = set()
        for node in ast.walk(func_node):
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node is not func_node
            ):
                for desc in ast.walk(node):
                    descendants.add(desc)
        return descendants
