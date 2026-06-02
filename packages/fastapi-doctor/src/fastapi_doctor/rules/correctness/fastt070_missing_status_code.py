import ast

from fastapi_doctor.rules.base import (
    Rule,
    register_rule,
    is_fastapi_endpoint,
)
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class MissingStatusCodeRule(Rule):
    """Detect POST/PUT/PATCH/DELETE endpoints missing explicit status_code (FASTT070)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT070",
            severity=Severity.WARNING,
            description="POST/PUT/PATCH/DELETE endpoint missing explicit status_code",
            recommendation="Add status_code parameter to the decorator (e.g., status_code=201 for POST)",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            method_name = is_fastapi_endpoint(node)
            if method_name is None or method_name == "get":
                continue

            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and method_name in (
                    "post",
                    "put",
                    "patch",
                    "delete",
                ):
                    if not self._has_status_code(decorator):
                        diagnostics.append(
                            Diagnostic(
                                severity=Severity.WARNING,
                                file_path=file_path,
                                rule=self.definition.id,
                                message=f"{method_name.upper()} endpoint '{node.name}' missing explicit status_code",
                                line=node.lineno,
                                column=node.col_offset,
                                help=self.definition.recommendation,
                            )
                        )
                    break

        return diagnostics

    def _has_status_code(self, decorator: ast.Call) -> bool:
        for keyword in decorator.keywords:
            if keyword.arg == "status_code":
                return True
        return False
