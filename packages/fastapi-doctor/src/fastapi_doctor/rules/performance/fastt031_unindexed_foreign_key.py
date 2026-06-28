import ast

from fastapi_doctor.rules.base import Rule, register_rule
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity

MODEL_COLUMN_FUNCTIONS = {"Column", "Field", "mapped_column"}


@register_rule
class UnindexedForeignKeyRule(Rule):
    """Detect ForeignKey columns without index=True (FASTT031).

    Covers SQLAlchemy Core (`Column`), SQLModel (`Field`), and SQLAlchemy 2.0 (`mapped_column`).
    """

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT031",
            severity=Severity.WARNING,
            description="ForeignKey column defined without index=True — missing index can cause slow JOINs",
            recommendation="Add index=True: Column(Integer, ForeignKey('t.id'), index=True) or Field(foreign_key='t.id', index=True)",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not self._is_model_column(node):
                continue
            if not self._has_foreign_key(node):
                continue
            if self._has_index_true(node):
                continue
            diagnostics.append(self._make_diag(node, file_path))
        return diagnostics

    def _is_model_column(self, node: ast.Call) -> bool:
        """Check if call is Column(), Field(), or mapped_column()."""
        if isinstance(node.func, ast.Name) and node.func.id in MODEL_COLUMN_FUNCTIONS:
            return True
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in MODEL_COLUMN_FUNCTIONS
        ):
            return True
        return False

    def _has_foreign_key(self, node: ast.Call) -> bool:
        """Check if the call contains a ForeignKey reference.

        Patterns:
            Column(Integer, ForeignKey("t.id"))     — ForeignKey() call in args
            Column(Integer, ForeignKey("t.id"))     — ForeignKey() call in keywords (rare)
            Field(foreign_key="t.id")               — foreign_key keyword string
            mapped_column(ForeignKey("t.id"))        — ForeignKey() call in args
        """
        for arg in node.args:
            if self._is_foreign_key_call(arg):
                return True
        for kw in node.keywords:
            if (
                kw.arg == "foreign_key"
                and isinstance(kw.value, ast.Constant)
                and isinstance(kw.value.value, str)
            ):
                return True
            if self._is_foreign_key_call(kw.value):
                return True
        return False

    def _is_foreign_key_call(self, node: ast.expr) -> bool:
        """Check if node is a ForeignKey() constructor call."""
        if not isinstance(node, ast.Call):
            return False
        if isinstance(node.func, ast.Name) and node.func.id == "ForeignKey":
            return True
        if isinstance(node.func, ast.Attribute) and node.func.attr == "ForeignKey":
            return True
        return False

    def _has_index_true(self, node: ast.Call) -> bool:
        """Check if the call has index=True as a literal keyword."""
        for kw in node.keywords:
            if (
                kw.arg == "index"
                and isinstance(kw.value, ast.Constant)
                and kw.value.value is True
            ):
                return True
        return False

    def _make_diag(self, node: ast.Call, file_path: str) -> Diagnostic:
        func_name = (
            node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        )
        return Diagnostic(
            severity=self.definition.severity,
            file_path=file_path,
            rule=self.definition.id,
            message=f"ForeignKey found in {func_name}() without index=True — add index=True for query performance",
            line=node.lineno,
            column=node.col_offset,
            help=self.definition.recommendation,
        )

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, ast.Call):
                continue
            if not self._is_model_column(node):
                continue
            if not self._has_foreign_key(node):
                continue
            if self._has_index_true(node):
                continue
            diagnostics.append(self._make_diag(node, file_path))
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
