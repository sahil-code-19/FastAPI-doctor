import ast

from fastapi_doctor.rules.base import Rule, register_rule, is_fastapi_endpoint
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class BackgroundTasksCeleryRule(Rule):
    """Detect BackgroundTasks used to wrap Celery tasks (FASTT034)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT034",
            severity=Severity.WARNING,
            description="BackgroundTasks is being used with Celery — use Celery directly or choose one async task system",
            recommendation="Call Celery tasks directly via .delay() or .apply_async() instead of wrapping them in BackgroundTasks",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        if not self._imports_celery(tree):
            return diagnostics

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            bg_param = self._find_bg_param(node)
            if bg_param is None:
                continue
            if self._calls_add_task(node, bg_param):
                diagnostics.append(
                    Diagnostic(
                        severity=self.definition.severity,
                        file_path=file_path,
                        rule=self.definition.id,
                        message=f"Endpoint '{node.name}' uses BackgroundTasks with Celery imports — use celery_task.delay() directly instead",
                        line=node.lineno,
                        column=node.col_offset,
                        help=self.definition.recommendation,
                    )
                )
        return diagnostics

    def _imports_celery(self, tree: ast.Module) -> bool:
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if "celery" in alias.name.lower():
                        return True
            if isinstance(node, ast.ImportFrom):
                if node.module and "celery" in node.module.lower():
                    return True
        return False

    def _find_bg_param(self, func_node) -> str | None:
        for arg in func_node.args.args:
            if (
                arg.annotation
                and isinstance(arg.annotation, ast.Name)
                and arg.annotation.id == "BackgroundTasks"
            ):
                return arg.arg
        return None

    def _calls_add_task(self, func_node, param_name: str) -> bool:
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "add_task":
                    if (
                        isinstance(node.func.value, ast.Name)
                        and node.func.value.id == param_name
                    ):
                        return True
        return False

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        if not self._imports_celery(tree):
            return diagnostics

        for node in nodes:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            bg_param = self._find_bg_param(node)
            if bg_param is None:
                continue
            if self._calls_add_task(node, bg_param):
                diagnostics.append(
                    Diagnostic(
                        severity=self.definition.severity,
                        file_path=file_path,
                        rule=self.definition.id,
                        message=f"Endpoint '{node.name}' uses BackgroundTasks with Celery imports — use celery_task.delay() directly instead",
                        line=node.lineno,
                        column=node.col_offset,
                        help=self.definition.recommendation,
                    )
                )
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
