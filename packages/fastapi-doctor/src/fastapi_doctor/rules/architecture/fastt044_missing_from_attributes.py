import ast

from fastapi_doctor.rules.base import Rule, register_rule
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity

DB_FIELD_NAMES = {
    "id",
    "created_at",
    "updated_at",
    "deleted_at",
    "is_active",
    "is_deleted",
}


@register_rule
class MissingFromAttributesRule(Rule):
    """Detect Pydantic models with DB-like fields but missing ConfigDict(from_attributes=True) (FASTT044)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT044",
            severity=Severity.WARNING,
            description="Pydantic model has DB-like fields but missing `model_config = ConfigDict(from_attributes=True)` — ORM mode not enabled",
            recommendation="Add `model_config = ConfigDict(from_attributes=True)` to the model class, or add `class Config: orm_mode = True` (v1)",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not self._inherits_from_basemodel(node):
                continue
            if self._has_from_attributes(node):
                continue
            if not self._has_db_like_fields(node):
                continue
            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message=f"class '{node.name}' has DB-like fields but missing ConfigDict(from_attributes=True)",
                    line=node.lineno,
                    column=node.col_offset,
                    help=self.definition.recommendation,
                )
            )
        return diagnostics

    def _inherits_from_basemodel(self, class_node: ast.ClassDef) -> bool:
        for base in class_node.bases:
            if isinstance(base, ast.Name) and base.id == "BaseModel":
                return True
        return False

    def _has_from_attributes(self, class_node: ast.ClassDef) -> bool:
        for item in class_node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == "model_config":
                        if isinstance(item.value, ast.Call):
                            if (
                                isinstance(item.value.func, ast.Name)
                                and item.value.func.id == "ConfigDict"
                            ):
                                for kw in item.value.keywords:
                                    if kw.arg == "from_attributes" and self._is_truthy(
                                        kw.value
                                    ):
                                        return True
            if isinstance(item, ast.ClassDef) and item.name == "Config":
                for sub in item.body:
                    if isinstance(sub, ast.Assign):
                        for target in sub.targets:
                            if isinstance(target, ast.Name) and target.id == "orm_mode":
                                if (
                                    isinstance(sub.value, ast.Constant)
                                    and sub.value.value is True
                                ):
                                    return True
        return False

    def _has_db_like_fields(self, class_node: ast.ClassDef) -> bool:
        db_field_count = 0
        for item in class_node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                if item.target.id in DB_FIELD_NAMES:
                    db_field_count += 1
        return db_field_count >= 2

    def _is_truthy(self, expr: ast.expr) -> bool:
        if isinstance(expr, ast.Constant):
            return bool(expr.value)
        return True

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, ast.ClassDef):
                continue
            if not self._inherits_from_basemodel(node):
                continue
            if self._has_from_attributes(node):
                continue
            if not self._has_db_like_fields(node):
                continue
            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message=f"class '{node.name}' has DB-like fields but missing ConfigDict(from_attributes=True)",
                    line=node.lineno,
                    column=node.col_offset,
                    help=self.definition.recommendation,
                )
            )
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
