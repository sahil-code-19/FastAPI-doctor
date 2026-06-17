import ast

from fastapi_doctor.rules.base import Rule, register_rule, is_fastapi_endpoint
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class UnusedRequestParamRule(Rule):
    """Detect `request: Request` parameter in routes where request is never used (FASTT026)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT026",
            severity=Severity.WARNING,
            description="Unused `request: Request` parameter in route handler — may indicate unnecessary dependency",
            recommendation="Remove the request parameter if not needed, or use request.state/request.headers in the body",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            request_params = self._find_request_params(node)
            if not request_params:
                continue
            used_names = self._collect_used_names_in_body(node)
            for param_name in request_params:
                if param_name not in used_names:
                    diagnostics.append(
                        Diagnostic(
                            severity=self.definition.severity,
                            file_path=file_path,
                            rule=self.definition.id,
                            message=f"unused 'request: Request' parameter '{param_name}' in endpoint '{node.name}'",
                            line=node.lineno,
                            column=node.col_offset,
                            help=self.definition.recommendation,
                        )
                    )
        return diagnostics

    def _find_request_params(self, func_node) -> list[str]:
        request_params = []
        for arg in func_node.args.args:
            if arg.annotation is None:
                continue
            if isinstance(arg.annotation, ast.Name) and arg.annotation.id == "Request":
                request_params.append(arg.arg)
            elif (
                isinstance(arg.annotation, ast.Attribute)
                and arg.annotation.attr == "Request"
            ):
                request_params.append(arg.arg)
        return request_params

    def _collect_used_names_in_body(self, func_node) -> set[str]:
        used = set()
        for child in ast.walk(func_node):
            if child is func_node:
                continue
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if isinstance(child, ast.Name):
                used.add(child.id)
            elif isinstance(child, ast.Attribute):
                if isinstance(child.value, ast.Name):
                    used.add(child.value.id)
        return used

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            request_params = self._find_request_params(node)
            if not request_params:
                continue
            used_names = self._collect_used_names_in_body(node)
            for param_name in request_params:
                if param_name not in used_names:
                    diagnostics.append(
                        Diagnostic(
                            severity=self.definition.severity,
                            file_path=file_path,
                            rule=self.definition.id,
                            message=f"unused 'request: Request' parameter '{param_name}' in endpoint '{node.name}'",
                            line=node.lineno,
                            column=node.col_offset,
                            help=self.definition.recommendation,
                        )
                    )
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
