import ast

from fastapi_doctor.rules.base import Rule, register_rule
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class DebugTrueNonTestFile(Rule):
    """Detect debug=True in non-test files — FastAPI(debug=True) or uvicorn.run(debug=True) (FASTT014)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT014",
            severity=Severity.WARNING,
            description="debug=True in FastAPI() or uvicorn.run() committed to non-test file — exposes tracebacks in production",
            recommendation="Remove debug=True or control it via environment variable (e.g. debug=os.getenv('DEBUG', False))",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            if self._is_fastapi_constructor(node) or self._is_uvicorn_run(node):
                diagnostics.extend(self._check_debug_keyword(node, file_path))

        return diagnostics

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, ast.Call):
                continue

            if self._is_fastapi_constructor(node) or self._is_uvicorn_run(node):
                diagnostics.extend(self._check_debug_keyword(node, file_path))

        return diagnostics

    def check_function(self, func_node, file_path):
        return []

    def _is_fastapi_constructor(self, call: ast.Call) -> bool:
        """Check if call is FastAPI(...)."""
        return isinstance(call.func, ast.Name) and call.func.id == "FastAPI"

    def _is_uvicorn_run(self, call: ast.Call) -> bool:
        """Check if call is uvicorn.run(...)."""
        return (
            isinstance(call.func, ast.Attribute)
            and call.func.attr == "run"
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id == "uvicorn"
        )

    def _check_debug_keyword(self, call: ast.Call, file_path: str) -> list[Diagnostic]:
        """Check if call has debug=True keyword."""
        for kw in call.keywords:
            if (
                kw.arg == "debug"
                and isinstance(kw.value, ast.Constant)
                and kw.value.value is True
            ):
                return [
                    Diagnostic(
                        severity=Severity.WARNING,
                        file_path=file_path,
                        rule=self.definition.id,
                        message="debug=True found in non-test file — should not be enabled in production",
                        line=call.lineno,
                        column=call.col_offset,
                        help=self.definition.recommendation,
                    )
                ]
        return []
