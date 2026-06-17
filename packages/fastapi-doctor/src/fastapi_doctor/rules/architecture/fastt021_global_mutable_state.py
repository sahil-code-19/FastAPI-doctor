import ast

from fastapi_doctor.rules.base import Rule, register_rule, is_fastapi_endpoint
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class GlobalMutableStateRule(Rule):
    """Detect global variable mutation inside route handlers — race condition risk (FASTT021)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT021",
            severity=Severity.WARNING,
            description="Global mutable state being modified inside a route handler — race condition risk in concurrent requests",
            recommendation="Use request-scoped state (request.state), database, or external cache instead of global variables",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            global_vars = self._collect_global_names(node)
            if not global_vars:
                continue
            for child in ast.walk(node):
                if child is node:
                    continue
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                mutated = self._get_mutated_global(child, global_vars)
                if mutated:
                    diagnostics.append(
                        Diagnostic(
                            severity=self.definition.severity,
                            file_path=file_path,
                            rule=self.definition.id,
                            message=f"global variable '{mutated}' mutated inside endpoint '{node.name}' — race condition risk",
                            line=child.lineno,
                            column=child.col_offset,
                            help=self.definition.recommendation,
                        )
                    )
        return diagnostics

    def _collect_global_names(self, func_node) -> set[str]:
        global_vars = set()
        for child in ast.walk(func_node):
            if isinstance(child, ast.Global):
                for name in child.names:
                    global_vars.add(name)
        return global_vars

    def _get_mutated_global(self, node: ast.AST, global_vars: set[str]) -> str | None:
        if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            if node.target.id in global_vars:
                return node.target.id
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in global_vars:
                    return target.id
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and isinstance(
                node.func.value, ast.Name
            ):
                if node.func.value.id in global_vars:
                    return node.func.value.id
            if isinstance(node.func, ast.Attribute) and isinstance(
                node.func.value, ast.Subscript
            ):
                if (
                    isinstance(node.func.value.value, ast.Name)
                    and node.func.value.value.id in global_vars
                ):
                    return node.func.value.value.id
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            if node.value.id in global_vars:
                parent = getattr(node, "_mutate_parent", None)
        return None

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            global_vars = self._collect_global_names(node)
            if not global_vars:
                continue
            for child in ast.walk(node):
                if child is node:
                    continue
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                mutated = self._get_mutated_global(child, global_vars)
                if mutated:
                    diagnostics.append(
                        Diagnostic(
                            severity=self.definition.severity,
                            file_path=file_path,
                            rule=self.definition.id,
                            message=f"global variable '{mutated}' mutated inside endpoint '{node.name}' — race condition risk",
                            line=child.lineno,
                            column=child.col_offset,
                            help=self.definition.recommendation,
                        )
                    )
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
