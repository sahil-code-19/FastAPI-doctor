import ast

from fastapi_doctor.rules.base import Rule, register_rule
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity

ROUTE_METHODS = {"get", "post", "put", "patch", "delete"}


@register_rule
class GodFilePatternRule(Rule):
    """Detect files where FastAPI() and 5+ routes are defined without include_router() (FASTT022)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT022",
            severity=Severity.WARNING,
            description="File defines FastAPI() and 5+ routes without using include_router() — consider splitting into routers",
            recommendation="Move routes into separate APIRouter modules and use app.include_router() to keep the main file lean",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        fastapi_vars = self._collect_fastapi_vars(tree)
        if not fastapi_vars:
            return diagnostics

        route_count = self._count_route_decorators(tree, fastapi_vars)
        if route_count < 5:
            return diagnostics

        if self._has_include_router(tree):
            return diagnostics

        for var_node in fastapi_vars:
            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message=f"FastAPI app defined with {route_count} routes in same file — use include_router() to split routes into modules",
                    line=var_node.lineno,
                    column=var_node.col_offset,
                    help=self.definition.recommendation,
                )
            )
        return diagnostics

    def _collect_fastapi_vars(self, tree: ast.Module) -> list[ast.Assign]:
        vars_ = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                if (
                    isinstance(node.value.func, ast.Name)
                    and node.value.func.id == "FastAPI"
                ):
                    vars_.append(node)
        return vars_

    def _count_route_decorators(
        self, tree: ast.Module, fastapi_vars: list[ast.Assign]
    ) -> int:
        var_names = set()
        for v in fastapi_vars:
            for target in v.targets:
                if isinstance(target, ast.Name):
                    var_names.add(target.id)

        count = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call) and isinstance(
                        decorator.func, ast.Attribute
                    ):
                        if decorator.func.attr in ROUTE_METHODS:
                            if (
                                isinstance(decorator.func.value, ast.Name)
                                and decorator.func.value.id in var_names
                            ):
                                count += 1
        return count

    def _has_include_router(self, tree: ast.Module) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "include_router"
                ):
                    return True
                if isinstance(node.func, ast.Name) and node.func.id == "include_router":
                    return True
        return False

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        fastapi_vars = [
            n
            for n in nodes
            if isinstance(n, ast.Assign)
            and isinstance(n.value, ast.Call)
            and isinstance(n.value.func, ast.Name)
            and n.value.func.id == "FastAPI"
        ]
        if not fastapi_vars:
            return diagnostics

        route_count = self._count_route_decorators_from_nodes(nodes, fastapi_vars)
        if route_count < 5:
            return diagnostics

        if self._has_include_router(tree):
            return diagnostics

        for var_node in fastapi_vars:
            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message=f"FastAPI app defined with {route_count} routes in same file — use include_router() to split routes into modules",
                    line=var_node.lineno,
                    column=var_node.col_offset,
                    help=self.definition.recommendation,
                )
            )
        return diagnostics

    def _count_route_decorators_from_nodes(self, nodes, fastapi_vars):
        var_names = set()
        for v in fastapi_vars:
            for target in v.targets:
                if isinstance(target, ast.Name):
                    var_names.add(target.id)
        count = 0
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call) and isinstance(
                        decorator.func, ast.Attribute
                    ):
                        if decorator.func.attr in ROUTE_METHODS:
                            if (
                                isinstance(decorator.func.value, ast.Name)
                                and decorator.func.value.id in var_names
                            ):
                                count += 1
        return count

    def check_function(self, func_node, file_path):
        return []
