import ast

from fastapi_doctor.rules.base import Rule, register_rule
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity

AUTH_FUNC_NAMES = {
    "get_current_user",
    "get_current_active_user",
    "require_user",
    "verify_token",
    "authenticate_user",
    "get_current_superuser",
}
ROUTE_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


@register_rule
class RouteLevelAuthRule(Rule):
    """Detect auth dependencies on individual routes instead of at the router level (FASTT053)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT053",
            severity=Severity.WARNING,
            description="Auth dependency set on individual routes but not at the APIRouter level — repeated and error-prone",
            recommendation="Move the auth dependency to the APIRouter: `router = APIRouter(dependencies=[Depends(get_current_user)])`",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        route_auth_funcs = self._collect_route_auth_depends(tree)
        if not route_auth_funcs:
            return diagnostics

        router_auth_funcs = self._collect_router_auth_depends(tree)
        missing_at_router = route_auth_funcs - router_auth_funcs
        if not missing_at_router:
            return diagnostics

        first_lines = self._find_first_route_auth_lines(tree, missing_at_router)
        for auth_func, line_no, col_no in first_lines:
            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message=f"Auth dependency 'Depends({auth_func})' found on individual routes but missing from router-level dependencies",
                    line=line_no,
                    column=col_no,
                    help=self.definition.recommendation,
                )
            )
        return diagnostics

    def _collect_route_auth_depends(self, tree: ast.Module) -> set[str]:
        auth_funcs = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    if not isinstance(decorator, ast.Call):
                        continue
                    if not isinstance(decorator.func, ast.Attribute):
                        continue
                    if decorator.func.attr not in ROUTE_METHODS:
                        continue
                    auth_funcs.update(self._extract_auth_from_decorator_deps(decorator))
                    auth_funcs.update(self._extract_auth_from_params(node))
        return auth_funcs

    def _collect_router_auth_depends(self, tree: ast.Module) -> set[str]:
        auth_funcs = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if (
                    isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id == "APIRouter"
                ):
                    for kw in node.value.keywords:
                        if kw.arg == "dependencies":
                            auth_funcs.update(self._extract_auth_names(kw.value))
        return auth_funcs

    def _extract_auth_from_decorator_deps(self, decorator: ast.Call) -> set[str]:
        result = set()
        for kw in decorator.keywords:
            if kw.arg == "dependencies":
                result.update(self._extract_auth_names(kw.value))
        return result

    def _extract_auth_from_params(self, func_node) -> set[str]:
        result = set()
        for arg in func_node.args.args:
            if arg.annotation and isinstance(arg.annotation, ast.Call):
                dep_name = self._get_depends_func(arg.annotation)
                if dep_name and dep_name in AUTH_FUNC_NAMES:
                    result.add(dep_name)
            if arg.annotation and isinstance(arg.annotation, ast.Attribute):
                inner = arg.annotation.value
                if (
                    isinstance(inner, ast.Call)
                    and isinstance(inner.func, ast.Name)
                    and inner.func.id == "Depends"
                ):
                    if (
                        inner.args
                        and isinstance(inner.args[0], ast.Name)
                        and inner.args[0].id in AUTH_FUNC_NAMES
                    ):
                        result.add(inner.args[0].id)
        for default in func_node.args.defaults:
            if (
                isinstance(default, ast.Call)
                and isinstance(default.func, ast.Name)
                and default.func.id == "Depends"
            ):
                if (
                    default.args
                    and isinstance(default.args[0], ast.Name)
                    and default.args[0].id in AUTH_FUNC_NAMES
                ):
                    result.add(default.args[0].id)
        return result

    def _get_depends_func(self, call_node: ast.Call) -> str | None:
        func = call_node.func
        is_annotated = (
            isinstance(func, ast.Name) and func.id == "Annotated"           # direct import
            or isinstance(func, ast.Attribute) and func.attr == "Annotated" # typing.Annotated
        )
        if not is_annotated:
            return None
        for arg in call_node.args[1:]:
            if (
                isinstance(arg, ast.Call)
                and isinstance(arg.func, ast.Name)
                and arg.func.id == "Depends"
            ):
                if arg.args and isinstance(arg.args[0], ast.Name):
                    return arg.args[0].id
        return None

    def _extract_auth_names(self, node: ast.expr) -> set[str]:
        names = set()
        if isinstance(node, ast.List):
            for item in node.elts:
                names.update(self._extract_auth_names(item))
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "Depends":
                if node.args and isinstance(node.args[0], ast.Name):
                    if node.args[0].id in AUTH_FUNC_NAMES:
                        names.add(node.args[0].id)
        return names

    def _find_first_route_auth_lines(
        self, tree: ast.Module, missing: set[str]
    ) -> list[tuple[str, int, int]]:
        result = []
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    if not isinstance(decorator, ast.Call):
                        continue
                    if not isinstance(decorator.func, ast.Attribute):
                        continue
                    if decorator.func.attr not in ROUTE_METHODS:
                        continue
                    for kw in decorator.keywords:
                        if kw.arg == "dependencies":
                            dep_funcs = self._extract_auth_names(kw.value)
                            for df in dep_funcs & missing:
                                if df not in found:
                                    found.add(df)
                                    result.append(
                                        (df, decorator.lineno, decorator.col_offset)
                                    )
                for arg in node.args.args:
                    if arg.annotation and isinstance(arg.annotation, ast.Call):
                        dep_name = self._get_depends_func(arg.annotation)
                        if dep_name and dep_name in missing and dep_name not in found:
                            found.add(dep_name)
                            result.append((dep_name, node.lineno, node.col_offset))
                for default in node.args.defaults:
                    if (
                        isinstance(default, ast.Call)
                        and isinstance(default.func, ast.Name)
                        and default.func.id == "Depends"
                    ):
                        if default.args and isinstance(default.args[0], ast.Name):
                            dep_name = default.args[0].id
                            if dep_name in missing and dep_name not in found:
                                found.add(dep_name)
                                result.append((dep_name, node.lineno, node.col_offset))
        return result

    def check_from_nodes(self, nodes, tree, file_path, source):
        return self.check(tree, file_path, source)

    def check_function(self, func_node, file_path):
        return []
