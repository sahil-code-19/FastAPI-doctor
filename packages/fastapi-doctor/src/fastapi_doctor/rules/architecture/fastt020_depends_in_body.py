import ast

from fastapi_doctor.rules.base import Rule, register_rule, is_fastapi_endpoint
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class DependsInBodyRule(Rule):
    """Detect `Depends(...)` used inside endpoint body instead of as parameter default (FASTT020)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT020",
            severity=Severity.ERROR,
            description="Depends() called inside endpoint body instead of as a parameter default — dependency injection should be at the parameter level",
            recommendation="Move Depends() to the function parameter: `db: Session = Depends(get_db)`",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            param_default_nodes = self._collect_param_default_nodes(node)
            for child in ast.walk(node):
                if child is node:
                    continue
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if child in param_default_nodes:
                    continue
                if not isinstance(child, ast.Call):
                    continue
                if not isinstance(child.func, ast.Name):
                    continue
                if child.func.id != "Depends":
                    continue
                diagnostics.append(
                    Diagnostic(
                        severity=self.definition.severity,
                        file_path=file_path,
                        rule=self.definition.id,
                        message=f"Depends() found in body of '{node.name}' — should be a parameter default instead",
                        line=child.lineno,
                        column=child.col_offset,
                        help=self.definition.recommendation,
                    )
                )
        return diagnostics

    def _collect_param_default_nodes(self, func_node) -> set:
        nodes = set()
        for default in func_node.args.defaults:
            for desc in ast.walk(default):
                nodes.add(desc)
        for kw_default in func_node.args.kw_defaults:
            if kw_default is not None:
                for desc in ast.walk(kw_default):
                    nodes.add(desc)
        for arg in func_node.args.args:
            if arg.annotation is not None:
                for desc in ast.walk(arg.annotation):
                    nodes.add(desc)
        return nodes

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            param_default_nodes = self._collect_param_default_nodes(node)
            for child in ast.walk(node):
                if child is node:
                    continue
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if child in param_default_nodes:
                    continue
                if not isinstance(child, ast.Call):
                    continue
                if not isinstance(child.func, ast.Name):
                    continue
                if child.func.id != "Depends":
                    continue
                diagnostics.append(
                    Diagnostic(
                        severity=self.definition.severity,
                        file_path=file_path,
                        rule=self.definition.id,
                        message=f"Depends() found in body of '{node.name}' — should be a parameter default instead",
                        line=child.lineno,
                        column=child.col_offset,
                        help=self.definition.recommendation,
                    )
                )
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
