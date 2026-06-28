import ast

from fastapi_doctor.rules.base import Rule, register_rule
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity

ROUTE_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


@register_rule
class RepeatedDependsRule(Rule):
    """Detect the same Depends() repeated on 5+ individual routes instead of router-level (FASTT051)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT051",
            severity=Severity.WARNING,
            description="The same dependency is repeated on 5+ individual routes — set it once at the router level instead",
            recommendation="Move the repeated dependency to the APIRouter level: `router = APIRouter(dependencies=[Depends(get_db)])`",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        dep_counter = self._collect_route_depends(tree)
        flagged = set()

        for dep_name, (count, first_node) in dep_counter.items():
            if count < 5:
                continue
            if dep_name in flagged:
                continue
            flagged.add(dep_name)
            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message=f"Dependency 'Depends({dep_name})' repeated {count} times across routes — move to router-level dependencies",
                    line=first_node.lineno,
                    column=first_node.col_offset,
                    help=self.definition.recommendation,
                )
            )
        return diagnostics

    def _collect_route_depends(
        self, tree: ast.Module
    ) -> dict[str, tuple[int, ast.AST]]:
        dep_counter: dict[str, tuple[int, ast.AST]] = {}

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
                            dep_names = self._extract_depends_names(kw.value)
                            for dep_name in dep_names:
                                if dep_name not in dep_counter:
                                    dep_counter[dep_name] = (0, decorator)
                                count, orig = dep_counter[dep_name]
                                dep_counter[dep_name] = (count + 1, orig)

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for arg in node.args.args:
                    if arg.annotation is not None:
                        dep_name = self._extract_depends_from_annotation(arg.annotation)
                        if dep_name:
                            if dep_name not in dep_counter:
                                dep_counter[dep_name] = (0, node)
                            count, orig = dep_counter[dep_name]
                            dep_counter[dep_name] = (count + 1, orig)

                for default in node.args.defaults:
                    dep_name = self._extract_depends_from_default(default)
                    if dep_name:
                        if dep_name not in dep_counter:
                            dep_counter[dep_name] = (0, node)
                        count, orig = dep_counter[dep_name]
                        dep_counter[dep_name] = (count + 1, orig)

        return dep_counter

    def _extract_depends_names(self, node: ast.expr) -> set[str]:
        names = set()
        if isinstance(node, ast.List):
            for item in node.elts:
                names.update(self._extract_depends_names(item))
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "Depends":
                if node.args and isinstance(node.args[0], ast.Name):
                    names.add(node.args[0].id)
        return names

    def _extract_depends_from_annotation(self, node: ast.expr) -> str | None:
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            inner = node.func.value
            if (
                isinstance(inner, ast.Call)
                and isinstance(inner.func, ast.Name)
                and inner.func.id == "Depends"
            ):
                if inner.args and isinstance(inner.args[0], ast.Name):
                    return inner.args[0].id
        return None

    def _extract_depends_from_default(self, node: ast.expr) -> str | None:
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "Depends"
        ):
            if node.args and isinstance(node.args[0], ast.Name):
                return node.args[0].id
        return None

    def check_from_nodes(self, nodes, tree, file_path, source):
        return self.check(tree, file_path, source)

    def check_function(self, func_node, file_path):
        return []
