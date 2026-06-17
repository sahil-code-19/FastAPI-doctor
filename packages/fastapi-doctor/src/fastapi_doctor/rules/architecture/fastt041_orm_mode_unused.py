import ast

from fastapi_doctor.rules.base import Rule, register_rule
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class OrmModeUnusedRule(Rule):
    """Detect orm_mode = True in Pydantic models that never call .from_orm() (FASTT041)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT041",
            severity=Severity.WARNING,
            description="Pydantic model has orm_mode = True but .from_orm() is never called in the same file — unused ORM configuration",
            recommendation="Remove orm_mode = True if .from_orm() is never used, or add .from_orm() calls to leverage ORM deserialization",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        orm_mode_classes = self._find_orm_mode_classes(tree)
        if not orm_mode_classes:
            return diagnostics

        if self._has_from_orm_call(tree):
            return diagnostics

        for cls_node in orm_mode_classes:
            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message=f"class '{cls_node.name}' has orm_mode = True but .from_orm() is never called in this file",
                    line=cls_node.lineno,
                    column=cls_node.col_offset,
                    help=self.definition.recommendation,
                )
            )
        return diagnostics

    def _find_orm_mode_classes(self, tree: ast.Module) -> list[ast.ClassDef]:
        classes = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not self._inherits_basemodel(node):
                continue
            if self._has_orm_mode(node):
                classes.append(node)
        return classes

    def _inherits_basemodel(self, class_node: ast.ClassDef) -> bool:
        for base in class_node.bases:
            if isinstance(base, ast.Name) and base.id == "BaseModel":
                return True
        return False

    def _has_orm_mode(self, class_node: ast.ClassDef) -> bool:
        for item in class_node.body:
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

    def _has_from_orm_call(self, tree: ast.Module) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "from_orm":
                    return True
        return False

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        orm_mode_classes = [
            n
            for n in nodes
            if isinstance(n, ast.ClassDef)
            and self._inherits_basemodel(n)
            and self._has_orm_mode(n)
        ]
        if not orm_mode_classes:
            return diagnostics

        if self._has_from_orm_call(tree):
            return diagnostics

        for cls_node in orm_mode_classes:
            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message=f"class '{cls_node.name}' has orm_mode = True but .from_orm() is never called in this file",
                    line=cls_node.lineno,
                    column=cls_node.col_offset,
                    help=self.definition.recommendation,
                )
            )
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
