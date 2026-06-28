import ast

from fastapi_doctor.rules.base import Rule, register_rule, is_fastapi_endpoint
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity

DB_CALL_METHODS = {"query", "execute", "get", "refresh", "scalars"}


@register_rule
class NPlusOneQueryRule(Rule):
    """Detect DB queries inside loops — N+1 query pattern (FASTT030)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT030",
            severity=Severity.ERROR,
            description="Database query inside a for loop — indicates an N+1 query pattern",
            recommendation="Use joinedload(), selectinload(), or batch query to eagerly load related data in a single query",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            for child in ast.walk(node):
                if (
                    isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and child is not node
                ):
                    continue
                if not isinstance(child, (ast.For, ast.AsyncFor)):
                    continue
                flagged = False
                for inner in ast.walk(child):
                    if isinstance(inner, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    if not isinstance(inner, ast.Call):
                        continue
                    if self._is_db_query_call(inner):
                        if not flagged:
                            diagnostics.append(
                                Diagnostic(
                                    severity=self.definition.severity,
                                    file_path=file_path,
                                    rule=self.definition.id,
                                    message=f"DB query inside for loop in endpoint '{node.name}' — potential N+1 query",
                                    line=child.lineno,
                                    column=child.col_offset,
                                    help=self.definition.recommendation,
                                )
                            )
                            flagged = True
                            break
        return diagnostics

    def _is_db_query_call(self, call_node: ast.Call) -> bool:
        if isinstance(call_node.func, ast.Attribute):
            if call_node.func.attr in DB_CALL_METHODS:
                return True
        return False

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            for child in ast.walk(node):
                if (
                    isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and child is not node
                ):
                    continue
                if not isinstance(child, (ast.For, ast.AsyncFor)):
                    continue
                flagged = False
                for inner in ast.walk(child):
                    if isinstance(inner, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    if not isinstance(inner, ast.Call):
                        continue
                    if self._is_db_query_call(inner):
                        if not flagged:
                            diagnostics.append(
                                Diagnostic(
                                    severity=self.definition.severity,
                                    file_path=file_path,
                                    rule=self.definition.id,
                                    message=f"DB query inside for loop in endpoint '{node.name}' — potential N+1 query",
                                    line=child.lineno,
                                    column=child.col_offset,
                                    help=self.definition.recommendation,
                                )
                            )
                            flagged = True
                            break
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
