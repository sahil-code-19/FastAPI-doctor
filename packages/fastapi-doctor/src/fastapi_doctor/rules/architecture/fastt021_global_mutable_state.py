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
        module_mutables = self._collect_module_level_mutables(tree)

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue

            global_vars = self._collect_global_names(node)
            target_names = module_mutables | global_vars

            for child in ast.walk(node):
                if child is node:
                    continue
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue

                name = self._get_mutated_name(child, target_names)
                if name:
                    diagnostics.append(
                        Diagnostic(
                            severity=self.definition.severity,
                            file_path=file_path,
                            rule=self.definition.id,
                            message=f"global variable '{name}' mutated inside endpoint '{node.name}' — race condition risk",
                            line=child.lineno,
                            column=child.col_offset,
                            help=self.definition.recommendation,
                        )
                    )
        return diagnostics

    def _collect_module_level_mutables(self, tree: ast.Module) -> set[str]:
        """Find module-level variables assigned to dict/list/set literals."""
        mutables = set()
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            if not isinstance(node.value, (ast.Dict, ast.List, ast.Set, ast.Call)):
                continue
            if isinstance(node.value, ast.Call):
                if not isinstance(node.value.func, ast.Name):
                    continue
                if node.value.func.id not in ("dict", "list", "set"):
                    continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    mutables.add(target.id)
        return mutables

    def _collect_global_names(self, func_node) -> set[str]:
        global_vars = set()
        for child in ast.walk(func_node):
            if isinstance(child, ast.Global):
                for name in child.names:
                    global_vars.add(name)
        return global_vars

    def _get_mutated_name(self, node: ast.AST, target_names: set[str]) -> str | None:
        # x = value (reassignment with global)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in target_names:
                    return target.id
        # x += 1 (augmented assign)
        if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            if node.target.id in target_names:
                return node.target.id
        # x.append(...), x.update(...), x.add(...), x.remove(...), x.pop(...), x.clear(...)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id in target_names:
                    if node.func.attr in (
                        "append",
                        "update",
                        "add",
                        "remove",
                        "pop",
                        "clear",
                        "extend",
                        "insert",
                        "discard",
                    ):
                        return node.func.value.id
        # x[key] = value (dict/list subscript assign) — detected via store context
        # For subscript mutation: global_mut["key"] = value
        # AST: Assign(targets=[Subscript(value=Name('global_mut'), ...)], value=...)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Subscript):
                    if (
                        isinstance(target.value, ast.Name)
                        and target.value.id in target_names
                    ):
                        return target.value.id
        return None

    def check_from_nodes(self, nodes, tree, file_path, source):
        return self.check(tree, file_path, source)

    def check_function(self, func_node, file_path):
        return []
