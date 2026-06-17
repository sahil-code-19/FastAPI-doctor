import ast

from fastapi_doctor.rules.base import Rule, register_rule, resolve_call_name
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity

RAW_DB_CONNECT = {
    "psycopg2.connect",
    "sqlite3.connect",
    "asyncpg.connect",
    "mysql.connector.connect",
    "pymysql.connect",
}


@register_rule
class RawDbConnectStartupRule(Rule):
    """Detect raw database connect() in startup/lifespan without connection pooling (FASTT024)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT024",
            severity=Severity.WARNING,
            description="Raw database connect() in startup without connection pooling — use SQLAlchemy engine with pool_size instead",
            recommendation="Use create_async_engine() with a connection pool (pool_size, max_overflow) instead of raw connect()",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not self._is_startup_or_lifespan(node):
                continue
            for child in ast.walk(node):
                if not isinstance(child, ast.Call):
                    continue
                call_name = resolve_call_name(child)
                if call_name is None:
                    continue
                if call_name in RAW_DB_CONNECT:
                    diagnostics.append(
                        Diagnostic(
                            severity=self.definition.severity,
                            file_path=file_path,
                            rule=self.definition.id,
                            message=f"raw database '{call_name}()' in startup without connection pooling",
                            line=child.lineno,
                            column=child.col_offset,
                            help=self.definition.recommendation,
                        )
                    )
        return diagnostics

    def _is_startup_or_lifespan(self, func_node) -> bool:
        for decorator in func_node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            if not isinstance(decorator.func, ast.Attribute):
                continue
            if decorator.func.attr == "on_event":
                return True
        if func_node.name in ("lifespan", "init_db", "startup", "create_db_and_tables"):
            return True
        return False

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not self._is_startup_or_lifespan(node):
                continue
            for child in ast.walk(node):
                if not isinstance(child, ast.Call):
                    continue
                call_name = resolve_call_name(child)
                if call_name is None:
                    continue
                if call_name in RAW_DB_CONNECT:
                    diagnostics.append(
                        Diagnostic(
                            severity=self.definition.severity,
                            file_path=file_path,
                            rule=self.definition.id,
                            message=f"raw database '{call_name}()' in startup without connection pooling",
                            line=child.lineno,
                            column=child.col_offset,
                            help=self.definition.recommendation,
                        )
                    )
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
