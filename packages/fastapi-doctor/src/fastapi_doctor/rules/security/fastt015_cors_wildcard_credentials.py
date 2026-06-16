import ast

from fastapi_doctor.rules.base import Rule, register_rule
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class CorsWildcardCredentialsRule(Rule):
    """Detect allow_origins=['*'] combined with allow_credentials=True (FASTT015)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT015",
            severity=Severity.ERROR,
            description="CORS configured with allow_origins=['*'] AND allow_credentials=True — credentials + wildcard origin is invalid",
            recommendation="Specify explicit allowed origins (never ['*']) when using allow_credentials=True",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            if self._is_cors_config(node):
                if self._has_wildcard_origins(node) and self._has_credentials_true(
                    node
                ):
                    diagnostics.append(
                        Diagnostic(
                            severity=Severity.ERROR,
                            file_path=file_path,
                            rule=self.definition.id,
                            message="allow_origins=['*'] with allow_credentials=True — browsers will reject this as invalid CORS",
                            line=node.lineno,
                            column=node.col_offset,
                            help=self.definition.recommendation,
                        )
                    )

        return diagnostics

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, ast.Call):
                continue

            if self._is_cors_config(node):
                if self._has_wildcard_origins(node) and self._has_credentials_true(
                    node
                ):
                    diagnostics.append(
                        Diagnostic(
                            severity=Severity.ERROR,
                            file_path=file_path,
                            rule=self.definition.id,
                            message="allow_origins=['*'] with allow_credentials=True — browsers will reject this as invalid CORS",
                            line=node.lineno,
                            column=node.col_offset,
                            help=self.definition.recommendation,
                        )
                    )

        return diagnostics

    def check_function(self, func_node, file_path):
        return []

    def _is_cors_config(self, call: ast.Call) -> bool:
        """Check if the Call is a CORS configuration."""
        # Pattern 1 & 2: app.add_middleware(CORSMiddleware, ...) or app.add_middleware("CORSMiddleware", ...)
        if isinstance(call.func, ast.Attribute) and call.func.attr == "add_middleware":
            if call.args:
                first_arg = call.args[0]
                if isinstance(first_arg, ast.Name) and first_arg.id == "CORSMiddleware":
                    return True
                if (
                    isinstance(first_arg, ast.Constant)
                    and first_arg.value == "CORSMiddleware"
                ):
                    return True

        # Pattern 3: FastAPI(allow_origins=..., ...)
        if isinstance(call.func, ast.Name) and call.func.id == "FastAPI":
            return True

        return False

    def _has_wildcard_origins(self, call: ast.Call) -> bool:
        """Check if allow_origins contains ['*']."""
        for kw in call.keywords:
            if kw.arg == "allow_origins" and isinstance(kw.value, ast.List):
                for elt in kw.value.elts:
                    if isinstance(elt, ast.Constant) and elt.value == "*":
                        return True
        return False

    def _has_credentials_true(self, call: ast.Call) -> bool:
        """Check if allow_credentials is set to True."""
        for kw in call.keywords:
            if kw.arg == "allow_credentials":
                if isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    return True
        return False
