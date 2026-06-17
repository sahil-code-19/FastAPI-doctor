import ast

from fastapi_doctor.rules.base import Rule, register_rule
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity

DEPRECATED_EVENTS = {"startup", "shutdown"}


@register_rule
class DeprecatedOnEventRule(Rule):
    """Detect deprecated @app.on_event('startup'/'shutdown') — use lifespan (FASTT025)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT025",
            severity=Severity.WARNING,
            description="Deprecated @app.on_event('startup'/'shutdown') — use lifespan context manager instead",
            recommendation="Replace with lifespan: app = FastAPI(lifespan=my_lifespan) using asynccontextmanager",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                if not isinstance(decorator.func, ast.Attribute):
                    continue
                if decorator.func.attr != "on_event":
                    continue
                if not decorator.args:
                    continue
                first_arg = decorator.args[0]
                if (
                    isinstance(first_arg, ast.Constant)
                    and first_arg.value in DEPRECATED_EVENTS
                ):
                    diagnostics.append(
                        Diagnostic(
                            severity=Severity.WARNING,
                            file_path=file_path,
                            rule=self.definition.id,
                            message=f"deprecated @app.on_event('{first_arg.value}') — use lifespan instead",
                            line=node.lineno,
                            column=node.col_offset,
                            help=self.definition.recommendation,
                        )
                    )
                    break
        return diagnostics

    def check_from_nodes(
        self, nodes: list[ast.AST], tree: ast.Module, file_path: str, source: str
    ) -> list[Diagnostic]:
        diagnostics = []
        for node in nodes:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                if not isinstance(decorator.func, ast.Attribute):
                    continue
                if decorator.func.attr != "on_event":
                    continue
                if not decorator.args:
                    continue
                first_arg = decorator.args[0]
                if (
                    isinstance(first_arg, ast.Constant)
                    and first_arg.value in DEPRECATED_EVENTS
                ):
                    diagnostics.append(
                        Diagnostic(
                            severity=Severity.WARNING,
                            file_path=file_path,
                            rule=self.definition.id,
                            message=f"deprecated @app.on_event('{first_arg.value}') — use lifespan instead",
                            line=node.lineno,
                            column=node.col_offset,
                            help=self.definition.recommendation,
                        )
                    )
                    break
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
