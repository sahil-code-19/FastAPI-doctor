import ast

from fastapi_doctor.rules.base import Rule, register_rule, is_fastapi_endpoint
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class FileInsteadOfUploadFileRule(Rule):
    """Detect using File instead of UploadFile in route parameters (FASTT027)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT027",
            severity=Severity.WARNING,
            description="Using `File` or `bytes = File()` reads entire file into memory — use UploadFile for streaming instead",
            recommendation="Replace with `file: UploadFile` for memory-efficient file handling",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            diagnostics.extend(self._check_params(node, file_path))
        return diagnostics

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            diagnostics.extend(self._check_params(node, file_path))
        return diagnostics

    def _check_params(self, func_node, file_path) -> list[Diagnostic]:
        diagnostics = []
        args = func_node.args.args
        defaults = func_node.args.defaults
        offset = len(args) - len(defaults)
        for i, arg in enumerate(args):
            if arg.annotation is None:
                continue
            if not isinstance(arg.annotation, ast.Name):
                continue
            ann_id = arg.annotation.id

            # Case 1: file: File (annotation directly is File class)
            if ann_id == "File":
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.WARNING,
                        file_path=file_path,
                        rule=self.definition.id,
                        message=f"parameter '{arg.arg}' uses File — prefer UploadFile for streaming",
                        line=arg.lineno,
                        column=arg.col_offset,
                        help=self.definition.recommendation,
                    )
                )
                continue

            # Case 2: file: bytes = File() (reads entire file into memory)
            if ann_id == "bytes":
                default_idx = i - offset
                if 0 <= default_idx < len(defaults):
                    default_node = defaults[default_idx]
                    if (
                        isinstance(default_node, ast.Call)
                        and isinstance(default_node.func, ast.Name)
                        and default_node.func.id == "File"
                    ):
                        diagnostics.append(
                            Diagnostic(
                                severity=Severity.WARNING,
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
