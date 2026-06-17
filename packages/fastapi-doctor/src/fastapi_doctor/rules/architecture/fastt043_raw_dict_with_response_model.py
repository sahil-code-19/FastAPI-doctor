import ast

from fastapi_doctor.rules.base import Rule, register_rule, is_fastapi_endpoint
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class RawDictWithResponseModelRule(Rule):
    """Detect returning a raw dict when response_model is set — Pydantic validation bypassed (FASTT043)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT043",
            severity=Severity.ERROR,
            description="Returning raw dict/list when response_model is set — Pydantic validation on response is bypassed",
            recommendation="Return the Pydantic model instance instead, or remove response_model if dict is intentional",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            has_response_model = self._has_response_model(node)
            if not has_response_model:
                continue
            for child in ast.walk(node):
                if child is node:
                    continue
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if not isinstance(child, ast.Return):
                    continue
                if child.value is None:
                    continue
                if isinstance(child.value, (ast.Dict, ast.List)):
                    diagnostics.append(
                        Diagnostic(
                            severity=self.definition.severity,
                            file_path=file_path,
                            rule=self.definition.id,
                            message=f"endpoint '{node.name}' returns a raw dict/list but has response_model set — validation bypassed",
                            line=child.lineno,
                            column=child.col_offset,
                            help=self.definition.recommendation,
                        )
                    )
        return diagnostics

    def _has_response_model(self, func_node) -> bool:
        for decorator in func_node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            for keyword in decorator.keywords:
                if keyword.arg == "response_model":
                    return True
        return False

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            has_response_model = self._has_response_model(node)
            if not has_response_model:
                continue
            for child in ast.walk(node):
                if child is node:
                    continue
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if not isinstance(child, ast.Return):
                    continue
                if child.value is None:
                    continue
                if isinstance(child.value, (ast.Dict, ast.List)):
                    diagnostics.append(
                        Diagnostic(
                            severity=self.definition.severity,
                            file_path=file_path,
                            rule=self.definition.id,
                            message=f"endpoint '{node.name}' returns a raw dict/list but has response_model set — validation bypassed",
                            line=child.lineno,
                            column=child.col_offset,
                            help=self.definition.recommendation,
                        )
                    )
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
