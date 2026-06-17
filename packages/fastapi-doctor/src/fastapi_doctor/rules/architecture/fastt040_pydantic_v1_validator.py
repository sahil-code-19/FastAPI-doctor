import ast

from fastapi_doctor.rules.base import Rule, register_rule
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class PydanticV1ValidatorRule(Rule):
    """Detect Pydantic v1 @validator decorators — should use @field_validator in v2 (FASTT040)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT040",
            severity=Severity.WARNING,
            description="Using Pydantic v1 @validator decorator — migrate to @field_validator in Pydantic v2",
            recommendation="Replace @validator('field') with @field_validator('field') and update method signatures",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if not isinstance(item, ast.FunctionDef):
                    continue
                is_classmethod = any(
                    isinstance(d, ast.Name) and d.id == "classmethod"
                    for d in item.decorator_list
                )
                for decorator in item.decorator_list:
                    if not isinstance(decorator, ast.Call):
                        continue
                    if not isinstance(decorator.func, ast.Name):
                        continue
                    if decorator.func.id != "validator":
                        continue
                    diagnostics.append(
                        Diagnostic(
                            severity=self.definition.severity,
                            file_path=file_path,
                            rule=self.definition.id,
                            message=f"v1-style @validator found on '{item.name}' in class '{node.name}' — use @field_validator instead",
                            line=item.lineno,
                            column=item.col_offset,
                            help=self.definition.recommendation,
                        )
                    )
        return diagnostics

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if not isinstance(item, ast.FunctionDef):
                    continue
                for decorator in item.decorator_list:
                    if not isinstance(decorator, ast.Call):
                        continue
                    if not isinstance(decorator.func, ast.Name):
                        continue
                    if decorator.func.id != "validator":
                        continue
                    diagnostics.append(
                        Diagnostic(
                            severity=self.definition.severity,
                            file_path=file_path,
                            rule=self.definition.id,
                            message=f"v1-style @validator found on '{item.name}' in class '{node.name}' — use @field_validator instead",
                            line=item.lineno,
                            column=item.col_offset,
                            help=self.definition.recommendation,
                        )
                    )
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
