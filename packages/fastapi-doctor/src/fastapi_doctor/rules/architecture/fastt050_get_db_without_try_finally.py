import ast

from fastapi_doctor.rules.base import Rule, register_rule
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class GetDbWithoutTryFinallyRule(Rule):
    """Detect `yield db` in dependency functions without try/finally — session leak risk (FASTT050)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT050",
            severity=Severity.ERROR,
            description="yield in dependency function without try/finally wrapping — database session may not be closed on error",
            recommendation="Wrap yield with try/finally to ensure session.close() is always called",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not self._has_yield(node):
                continue
            if self._yield_in_safe_context(node):
                continue
            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message=f"function '{node.name}' has yield without try/finally — session may leak on error",
                    line=node.lineno,
                    column=node.col_offset,
                    help=self.definition.recommendation,
                )
            )
        return diagnostics

    def _has_yield(self, func_node) -> bool:
        for child in ast.walk(func_node):
            if isinstance(child, (ast.Yield, ast.YieldFrom)):
                return True
        return False

    def _yield_in_safe_context(self, func_node) -> bool:
        """Check if yield is inside try/finally, with/async with, or asynccontextmanager."""
        if self._has_asynccontextmanager_decorator(func_node):
            return True
        for child in ast.walk(func_node):
            if isinstance(child, ast.Try) and child.finalbody:
                if any(
                    isinstance(h, (ast.Yield, ast.YieldFrom)) for h in ast.walk(child)
                ):
                    return True
            if isinstance(child, (ast.With, ast.AsyncWith)):
                if any(
                    isinstance(h, (ast.Yield, ast.YieldFrom)) for h in ast.walk(child)
                ):
                    return True
        return False

    def _has_asynccontextmanager_decorator(self, func_node) -> bool:
        for decorator in func_node.decorator_list:
            if (
                isinstance(decorator, ast.Name)
                and decorator.id == "asynccontextmanager"
            ):
                return True
            if (
                isinstance(decorator, ast.Attribute)
                and decorator.attr == "asynccontextmanager"
            ):
                return True
            if isinstance(decorator, ast.Call):
                if (
                    isinstance(decorator.func, ast.Name)
                    and decorator.func.id == "asynccontextmanager"
                ):
                    return True
        return False

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not self._has_yield(node):
                continue
            if self._yield_in_safe_context(node):
                continue
            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message=f"function '{node.name}' has yield without try/finally — session may leak on error",
                    line=node.lineno,
                    column=node.col_offset,
                    help=self.definition.recommendation,
                )
            )
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
