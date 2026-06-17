import ast

from fastapi_doctor.rules.base import Rule, register_rule
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity

SETTINGS_FUNC_NAMES = {"get_settings", "get_config", "load_settings"}


@register_rule
class MissingLruCacheRule(Rule):
    """Detect settings loader functions without @lru_cache decorator (FASTT036)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT036",
            severity=Severity.WARNING,
            description="Settings/config loader function is missing @lru_cache — repeated calls re-read and re-parse config",
            recommendation="Add @lru_cache or @cache decorator to cache settings: `from functools import lru_cache` then `@lru_cache`",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            if node.name not in SETTINGS_FUNC_NAMES:
                continue
            if self._has_cache_decorator(node):
                continue
            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message=f"Settings function '{node.name}' is missing @lru_cache — add caching to avoid repeated config parsing",
                    line=node.lineno,
                    column=node.col_offset,
                    help=self.definition.recommendation,
                )
            )
        return diagnostics

    def _has_cache_decorator(self, func_node: ast.FunctionDef) -> bool:
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id in {
                "lru_cache",
                "cache",
            }:
                return True
            if isinstance(decorator, ast.Attribute) and decorator.attr in {
                "lru_cache",
                "cache",
            }:
                return True
        return False

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, ast.FunctionDef):
                continue
            if node.name not in SETTINGS_FUNC_NAMES:
                continue
            if self._has_cache_decorator(node):
                continue
            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message=f"Settings function '{node.name}' is missing @lru_cache — add caching to avoid repeated config parsing",
                    line=node.lineno,
                    column=node.col_offset,
                    help=self.definition.recommendation,
                )
            )
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
