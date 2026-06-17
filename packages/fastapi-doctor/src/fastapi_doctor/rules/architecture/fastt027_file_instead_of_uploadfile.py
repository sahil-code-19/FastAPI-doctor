import ast

from fastapi_doctor.rules.base import Rule, register_rule, is_fastapi_endpoint
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class FileInsteadOfUploadFileRule(Rule):
    """Detect `file: bytes = File()` in route parameters — use UploadFile instead (FASTT027)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT027",
            severity=Severity.WARNING,
            description="Using `file: bytes = File()` reads entire file into memory — use UploadFile for streaming instead",
            recommendation="Replace `file: bytes = File()` with `file: UploadFile` for memory-efficient file handling",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            args = node.args.args
            defaults = node.args.defaults
            offset = len(args) - len(defaults)
            for i, arg in enumerate(args):
                if arg.annotation is None:
                    continue
                if not isinstance(arg.annotation, ast.Name):
                    continue
                if arg.annotation.id != "bytes":
                    continue
                default_idx = i - offset
                if default_idx < 0 or default_idx >= len(defaults):
                    continue
                default_node = defaults[default_idx]
                if not isinstance(default_node, ast.Call):
                    continue
                if not isinstance(default_node.func, ast.Name):
                    continue
                if default_node.func.id == "File":
                    diagnostics.append(
                        Diagnostic(
                            severity=self.definition.severity,
                            file_path=file_path,
                            rule=self.definition.id,
                            message=f"parameter '{arg.arg}' uses `bytes = File()` — use UploadFile instead",
                            line=arg.lineno,
                            column=arg.col_offset,
                            help=self.definition.recommendation,
                        )
                    )
        return diagnostics

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            args = node.args.args
            defaults = node.args.defaults
            offset = len(args) - len(defaults)
            for i, arg in enumerate(args):
                if arg.annotation is None:
                    continue
                if not isinstance(arg.annotation, ast.Name):
                    continue
                if arg.annotation.id != "bytes":
                    continue
                default_idx = i - offset
                if default_idx < 0 or default_idx >= len(defaults):
                    continue
                default_node = defaults[default_idx]
                if not isinstance(default_node, ast.Call):
                    continue
                if not isinstance(default_node.func, ast.Name):
                    continue
                if default_node.func.id == "File":
                    diagnostics.append(
                        Diagnostic(
                            severity=self.definition.severity,
                            file_path=file_path,
                            rule=self.definition.id,
                            message=f"parameter '{arg.arg}' uses `bytes = File()` — use UploadFile instead",
                            line=arg.lineno,
                            column=arg.col_offset,
                            help=self.definition.recommendation,
                        )
                    )
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
