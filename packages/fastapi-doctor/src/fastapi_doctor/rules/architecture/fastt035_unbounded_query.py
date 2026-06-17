import ast

from fastapi_doctor.rules.base import Rule, register_rule, is_fastapi_endpoint
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class UnboundedQueryRule(Rule):
    """Detect `db.query(Model).all()` without pagination inside route handlers (FASTT035)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT035",
            severity=Severity.ERROR,
            description="Unbounded database query (.all()/.scalars().all()) without limit/offset/pagination — can return excessive rows",
            recommendation="Add .limit() and .offset() for pagination, or use .paginate() if available",
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
                if not isinstance(child, ast.Call):
                    continue
                if not self._is_unbounded_all_call(child):
                    continue
                diagnostics.append(
                    Diagnostic(
                        severity=self.definition.severity,
                        file_path=file_path,
                        rule=self.definition.id,
                        message="unbounded DB query with .all() — add .limit()/.offset() for pagination",
                        line=child.lineno,
                        column=child.col_offset,
                        help=self.definition.recommendation,
                    )
                )
        return diagnostics

    def _is_unbounded_all_call(self, call_node: ast.Call) -> bool:
        if not isinstance(call_node.func, ast.Attribute):
            return False
        if call_node.func.attr not in {"all", "scalars"}:
            return False
        return self._has_query_method_in_chain(call_node)

    def _has_query_method_in_chain(self, call_node: ast.Call) -> bool:
        if isinstance(call_node.func, ast.Attribute) and call_node.func.attr == "query":
            return True
        if isinstance(call_node.func, ast.Attribute) and isinstance(
            call_node.func.value, ast.Call
        ):
            base = call_node.func.value
            chain_attr = getattr(base.func, "attr", None)
            if chain_attr in {"limit", "offset", "paginate"}:
                return False
            return self._has_query_method_in_chain(base)
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
                if not isinstance(child, ast.Call):
                    continue
                if not self._is_unbounded_all_call(child):
                    continue
                diagnostics.append(
                    Diagnostic(
                        severity=self.definition.severity,
                        file_path=file_path,
                        rule=self.definition.id,
                        message="unbounded DB query with .all() — add .limit()/.offset() for pagination",
                        line=child.lineno,
                        column=child.col_offset,
                        help=self.definition.recommendation,
                    )
                )
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
