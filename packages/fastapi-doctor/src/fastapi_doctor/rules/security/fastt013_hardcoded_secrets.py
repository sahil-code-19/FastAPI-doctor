import ast
import re

from fastapi_doctor.rules.base import Rule, register_rule
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity

# ── Secret name patterns (matched against variable names) ──────────────────
SECRET_NAME_PATTERNS = [
    "key",
    "secret",
    "token",
    "password",
    "passwd",
    "pwd",
    "api",
    "auth",
    "credential",
    "credentials",
    "salt",
    "signing",
    "private",
    "jwt",
    "session",
]

# ── Placeholder values (real strings that aren't real secrets) ─────────────
PLACEHOLDER_VALUES = {
    "",
    "changeme",
    "change-me",
    "change_me",
    "your-key-here",
    "your_token_here",
    "your-token-here",
    "your_secret_here",
    "your-secret-here",
    "replace-me",
    "replace_me",
    "TODO",
    "todo",
    "<your-key>",
    "<your-token>",
    "<key>",
    "<token>",
    "<password>",
}

# ── Known service key patterns (regex against string values) ───────────────
# Each entry: (pattern, label_for_error_message)
KNOWN_PATTERNS: list[tuple[str, str]] = [
    # GitHub tokens
    (r"^(?:ghp|gho|ghu|ghs)_[A-Za-z0-9_]{36}$", "GitHub Personal Access Token"),
    (r"^github_pat_[A-Za-z0-9_]{22,}$", "GitHub Fine-grained Token"),
    # OpenAI
    (r"^sk-(?:proj-)?[A-Za-z0-9_-]{20,}$", "OpenAI API Key"),
    # Anthropic
    (r"^sk-ant-api\d{2}-[A-Za-z0-9_-]{50,}$", "Anthropic API Key"),
    # Google
    (r"^AIza[0-9A-Za-z\-_]{35}$", "Google API Key"),
    # Stripe
    (r"^(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{20,}$", "Stripe Key"),
    # AWS
    (r"^AKIA[0-9A-Z]{16}$", "AWS Access Key ID"),
    # Slack
    (r"^xox[bp]-[A-Za-z0-9-]{20,}$", "Slack Token"),
    # PyPI
    (r"^pypi-AgEIcHlwaS5vcmc[A-Za-z0-9_-]{20,}$", "PyPI Token"),
    # JWT tokens
    (r"^eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}$", "JWT Token"),
]


@register_rule
class HardcodedSecretsRule(Rule):
    """Detect hardcoded secrets — AST variable names + regex key patterns (FASTT013)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT013",
            severity=Severity.ERROR,
            description="Hardcoded secret/key in source code — should be loaded from env or config",
            recommendation="Use os.environ.get('KEY') or settings.KEY instead of hardcoding secrets",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []

        for node in ast.walk(tree):
            # ─── PASS A: AST structural detection ─────────────────────────
            if isinstance(node, ast.Assign):
                diagnostics.extend(self._check_ast_assignment(node, file_path))

            # ─── PASS B: Regex pattern detection ─────────────────────────
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                diagnostics.extend(
                    self._check_regex_pattern(node.value, node, file_path)
                )

        return diagnostics

    def check_function(self, func_node, file_path):
        return []  # No import trace pass needed

    # ═══════════════════════════════════════════════════════════════════════
    #  PASS A helpers
    # ═══════════════════════════════════════════════════════════════════════

    def _check_ast_assignment(
        self, assign: ast.Assign, file_path: str
    ) -> list[Diagnostic]:
        """Check if an assignment like `SECRET_KEY = 'abc'` is hardcoded."""
        diagnostics = []

        for target in assign.targets:
            var_name = self._get_var_name(target)
            if var_name is None:
                continue

            if not self._is_secret_name(var_name):
                continue

            if self._is_safe_source(assign.value):
                continue

            if not isinstance(assign.value, ast.Constant) or not isinstance(
                assign.value.value, str
            ):
                continue

            value_str = assign.value.value

            if self._is_placeholder(value_str):
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.WARNING,
                        file_path=file_path,
                        rule=self.definition.id,
                        message=f"'{var_name}' is assigned a placeholder value — configure before deployment",
                        line=assign.lineno,
                        column=assign.col_offset,
                        help=self.definition.recommendation,
                    )
                )
                continue

            if self._is_too_short(value_str):
                continue

            if self._is_url(value_str):
                continue

            diagnostics.append(
                Diagnostic(
                    severity=Severity.ERROR,
                    file_path=file_path,
                    rule=self.definition.id,
                    message=f"Hardcoded secret detected: '{var_name}' — should be loaded from environment",
                    line=assign.lineno,
                    column=assign.col_offset,
                    help=self.definition.recommendation,
                )
            )

        return diagnostics

    def _get_var_name(self, target: ast.expr) -> str | None:
        """Extract variable name from an assignment target node."""
        if isinstance(target, ast.Name):
            return target.id
        return None

    def _is_secret_name(self, var_name: str) -> bool:
        """Check if variable name contains a secret-like pattern."""
        lower = var_name.lower()
        return any(pat in lower for pat in SECRET_NAME_PATTERNS)

    def _is_safe_source(self, value: ast.expr) -> bool:
        """Check if value is from a safe source (env var, config, etc.)."""
        # os.environ.get(...) or os.getenv(...)
        if isinstance(value, ast.Call):
            if isinstance(value.func, ast.Attribute):
                attr = value.func.attr
                base = value.func.value
                if attr in ("get", "getenv"):
                    if isinstance(base, ast.Attribute):
                        if (
                            base.attr == "environ"
                            and isinstance(base.value, ast.Name)
                            and base.value.id == "os"
                        ):
                            return True
                    if isinstance(base, ast.Name) and base.id == "os":
                        return True

        # settings.KEY or config.KEY
        if isinstance(value, ast.Attribute):
            if isinstance(value.value, ast.Name):
                if value.value.id in ("settings", "config"):
                    return True

        # os.environ['KEY']
        if isinstance(value, ast.Subscript):
            if isinstance(value.value, ast.Attribute):
                if value.value.attr == "environ" and isinstance(
                    value.value.value, ast.Name
                ):
                    if value.value.value.id == "os":
                        return True

        return False

    def _is_too_short(self, value_str: str) -> bool:
        """Skip strings too short to be real secrets (< 6 chars)."""
        return len(value_str) < 6

    def _is_url(self, value_str: str) -> bool:
        """Skip strings that look like URLs."""
        return "://" in value_str

    def _is_placeholder(self, value_str: str) -> bool:
        """Check if value is an obvious placeholder."""
        return value_str.strip() in PLACEHOLDER_VALUES

    # ═══════════════════════════════════════════════════════════════════════
    #  PASS B helpers
    # ═══════════════════════════════════════════════════════════════════════

    def _check_regex_pattern(
        self, value_str: str, node: ast.Constant, file_path: str
    ) -> list[Diagnostic]:
        """Check if a string literal matches a known service key pattern."""
        if len(value_str) < 10:
            return []

        for pattern, label in KNOWN_PATTERNS:
            if re.match(pattern, value_str):
                return [
                    Diagnostic(
                        severity=Severity.ERROR,
                        file_path=file_path,
                        rule=self.definition.id,
                        message=f"Hardcoded {label} detected — should not be in source code",
                        line=node.lineno,
                        column=node.col_offset,
                        help="Remove this key and load it from environment variables",
                    )
                ]

        return []
