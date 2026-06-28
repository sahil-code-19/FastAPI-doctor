import ast

from fastapi_doctor.rules.base import Rule, register_rule
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class SessionWithoutYieldRule(Rule):
    """Detect DB dependency functions that return Session instead of yielding it — session never closed (FASTT052)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT052",
            severity=Severity.WARNING,
            description="Function calls Session()/SessionLocal() and returns instead of yields — session is never properly closed",
            recommendation="Use `yield db` instead of `return db` to ensure FastAPI calls session.close() after the request",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            has_return = self._has_return(node)
            has_yield = self._has_yield(node)
            if not has_return or has_yield:
                continue
            if not self._calls_session(node):
                continue
            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message=f"function '{node.name}' calls Session() and returns — use yield instead for proper lifecycle",
                    line=node.lineno,
                    column=node.col_offset,
                    help=self.definition.recommendation,
                )
            )
        return diagnostics

    def _has_return(self, func_node) -> bool:
        for child in ast.walk(func_node):
            if (
                isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                and child is not func_node
            ):
                continue
            if isinstance(child, ast.Return) and child.value is not None:
                return True
        return False

    def _has_yield(self, func_node) -> bool:
        for child in ast.walk(func_node):
            if isinstance(child, (ast.Yield, ast.YieldFrom)):
                return True
        return False

    def _calls_session(self, func_node) -> bool:
        for child in ast.walk(func_node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name) and "Session" in child.func.id:
                    return True
                if (
                    isinstance(child.func, ast.Attribute)
                    and "Session" in child.func.attr
                ):
                    return True
        return False

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            has_return = self._has_return(node)
            has_yield = self._has_yield(node)
            if not has_return or has_yield:
                continue
            if not self._calls_session(node):
                continue
            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message=f"function '{node.name}' calls Session() and returns — use yield instead for proper lifecycle",
                    line=node.lineno,
                    column=node.col_offset,
                    help=self.definition.recommendation,
                )
            )
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
