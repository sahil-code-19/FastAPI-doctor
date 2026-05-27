import ast

from fastapi_doctor.rules.base import (
    Rule,
    register_rule,
    is_fastapi_endpoint,
    collect_threadpool_wrappers,
    is_inside_wrapper,
)
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity

DB_SESSION_METHODS = {
    "execute",
    "commit",
    "rollback",
    "query",
    "flush",
    "refresh",
    "merge",
    "delete",
    "bulk_save_objects",
    "bulk_insert_mappings",
    "scalars",
    "scalar",
}

ASYNC_RESULT_METHODS = {
    "scalars",
    "scalar",
    "fetchone",
    "fetchmany",
    "fetchall",
    "all",
    "first",
    "one",
    "one_or_none",
}


@register_rule
class DbSessionInAsyncRule(Rule):
    """Detect synchronous SQLAlchemy session calls in async FastAPI endpoints (FASTT002)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT002",
            severity=Severity.ERROR,
            description="Synchronous SQLAlchemy session call inside async endpoint — use AsyncSession instead",
            recommendation="Use AsyncSession with await (e.g. await session.execute()) or wrap in asyncio.to_thread()",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            diagnostics.extend(self._check_single(node, file_path))
        return diagnostics

    def check_function(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: str
    ) -> list[Diagnostic]:
        """Check a resolved function body (used by import trace pass)."""
        return self._check_single(func_node, file_path)

    def _check_single(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: str
    ) -> list[Diagnostic]:
        """Core check: find sync DB calls in a function body."""
        diagnostics = []
        wrappers = collect_threadpool_wrappers(func_node)

        decorator_descendants = self._collect_decorator_descendants(func_node)
        awaited_descendants = self._collect_awaited_descendants(func_node)
        inner_func_descendants = self._collect_inner_func_descendants(func_node)

        for child in ast.walk(func_node):
            if not isinstance(child, ast.Call):
                continue
            if not isinstance(child.func, ast.Attribute):
                continue
            if (
                child in decorator_descendants
                or child in awaited_descendants
                or child in inner_func_descendants
            ):
                continue

            method = child.func.attr
            if method not in DB_SESSION_METHODS:
                continue
            if method in ASYNC_RESULT_METHODS:
                continue
            if self._is_on_async_session(child):
                continue
            if is_inside_wrapper(child, wrappers):
                continue

            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message=f"Synchronous DB call '{method}()' inside async endpoint '{func_node.name}' — use await with AsyncSession",
                    line=child.lineno,
                    column=child.col_offset,
                    help=self.definition.recommendation,
                )
            )

        return diagnostics

    KNOWN_ASYNC_VARS = {"async_session", "async_db", "asession", "async_conn"}

    def _is_on_async_session(self, node: ast.Call) -> bool:
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                base_name = node.func.value.id.lower()
                if any(name in base_name for name in self.KNOWN_ASYNC_VARS):
                    return True
                if base_name.startswith("async_"):
                    return True
        return False

    def _collect_decorator_descendants(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> set[ast.AST]:
        descendants: set[ast.AST] = set()
        for decorator in func_node.decorator_list:
            for desc in ast.walk(decorator):
                descendants.add(desc)
        return descendants

    def _collect_awaited_descendants(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> set[ast.AST]:
        descendants: set[ast.AST] = set()
        for node in ast.walk(func_node):
            if isinstance(node, ast.Await):
                for desc in ast.walk(node):
                    descendants.add(desc)
        return descendants

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
