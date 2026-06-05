import ast

from fastapi_doctor.rules.base import Rule, register_rule
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class MissingHttpsRedirectMiddleware(Rule):
    """Detect missing HTTPSRedirectMiddleware in production-like settings (FASTT016)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT016",
            severity=Severity.WARNING,
            description="Missing HTTPSRedirectMiddleware in production-like settings",
            recommendation="Add HTTPSRedirectMiddleware via app.add_middleware(HTTPSRedirectMiddleware) for production",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        has_fastapi = False
        has_https = False
        fastapi_line = 0

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            if isinstance(node.func, ast.Name) and node.func.id == "FastAPI":
                has_fastapi = True
                fastapi_line = node.lineno

            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_middleware"
            ):
                if self._first_arg_is(node, "HTTPSRedirectMiddleware"):
                    has_https = True

        if has_fastapi and not has_https:
            return [
                Diagnostic(
                    severity=Severity.WARNING,
                    file_path=file_path,
                    rule=self.definition.id,
                    message="Missing HTTPSRedirectMiddleware — should be added for production",
                    line=fastapi_line,
                    column=0,
                    help=self.definition.recommendation,
                )
            ]

        return []

    def check_function(self, func_node, file_path):
        return []

    def _first_arg_is(self, call: ast.Call, name: str) -> bool:
        """Check if the first argument matches a given class name or string."""
        if not call.args:
            return False
        first = call.args[0]
        if isinstance(first, ast.Name) and first.id == name:
            return True
        if isinstance(first, ast.Constant) and first.value == name:
            return True
        return False
