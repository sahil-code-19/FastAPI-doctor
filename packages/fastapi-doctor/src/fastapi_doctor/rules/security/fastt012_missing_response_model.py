import ast

from fastapi_doctor.rules.base import Rule, register_rule, is_fastapi_endpoint
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class MissingResponseModelRule(Rule):
    """Detect GET endpoints missing response_model — untyped response (FASTT012)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT012",
            severity=Severity.WARNING,
            description="Missing response_model on GET endpoint — untyped response, no validation or docs schema",
            recommendation="Add response_model=<YourPydanticSchema> to the decorator",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            method_name = is_fastapi_endpoint(node)
            if method_name != "get":
                continue
            if self._has_response_model(node):
                continue
            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message=f"GET endpoint '{node.name}' missing response_model — untyped response",
                    line=node.lineno,
                    column=node.col_offset,
                    help=self.definition.recommendation,
                )
            )
        return diagnostics

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            method_name = is_fastapi_endpoint(node)
            if method_name != "get":
                continue
            if self._has_response_model(node):
                continue
            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message=f"GET endpoint '{node.name}' missing response_model — untyped response",
                    line=node.lineno,
                    column=node.col_offset,
                    help=self.definition.recommendation,
                )
            )
        return diagnostics

    def check_function(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: str
    ) -> list[Diagnostic]:
        return []

    def _has_response_model(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> bool:
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Call):
                for kw in decorator.keywords:
                    if kw.arg == "response_model":
                        return True
        return False
