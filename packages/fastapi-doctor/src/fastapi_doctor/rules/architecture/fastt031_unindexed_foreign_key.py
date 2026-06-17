import ast

from fastapi_doctor.rules.base import Rule, register_rule
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class UnindexedForeignKeyRule(Rule):
    """Detect ForeignKey columns without index=True (FASTT031)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT031",
            severity=Severity.WARNING,
            description="ForeignKey column defined without index=True — missing index can cause slow JOINs",
            recommendation="Add index=True to the Column() that contains ForeignKey(), e.g. Column(Integer, ForeignKey('t.id'), index=True)",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not self._is_column_call(node):
                continue
            if not self._has_foreignkey_arg(node):
                continue
            if self._has_index_keyword(node):
                continue
            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message="ForeignKey found in Column() without index=True — add index=True for query performance",
                    line=node.lineno,
                    column=node.col_offset,
                    help=self.definition.recommendation,
                )
            )
        return diagnostics

    def _is_column_call(self, node: ast.Call) -> bool:
        if isinstance(node.func, ast.Name) and node.func.id == "Column":
            return True
        if isinstance(node.func, ast.Attribute) and node.func.attr == "Column":
            return True
        return False

    def _has_foreignkey_arg(self, node: ast.Call) -> bool:
        for arg in node.args:
            if self._is_foreignkey_call(arg):
                return True
        for kw in node.keywords:
            if self._is_foreignkey_call(kw.value):
                return True
        return False

    def _is_foreignkey_call(self, node: ast.expr) -> bool:
        if not isinstance(node, ast.Call):
            return False
        if isinstance(node.func, ast.Name) and node.func.id == "ForeignKey":
            return True
        if isinstance(node.func, ast.Attribute) and node.func.attr == "ForeignKey":
            return True
        return False

    def _has_index_keyword(self, node: ast.Call) -> bool:
        for kw in node.keywords:
            if (
                kw.arg == "index"
                and isinstance(kw.value, ast.Constant)
                and kw.value.value is True
            ):
                return True
        return False

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, ast.Call):
                continue
            if not self._is_column_call(node):
                continue
            if not self._has_foreignkey_arg(node):
                continue
            if self._has_index_keyword(node):
                continue
            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message="ForeignKey found in Column() without index=True — add index=True for query performance",
                    line=node.lineno,
                    column=node.col_offset,
                    help=self.definition.recommendation,
                )
            )
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
