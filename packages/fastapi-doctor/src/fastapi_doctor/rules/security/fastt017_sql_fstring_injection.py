import ast

from fastapi_doctor.rules.base import Rule, register_rule
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity

SQL_KEYWORDS = {
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "FROM",
    "WHERE",
    "JOIN",
    "DROP",
    "CREATE",
    "ALTER",
    "EXEC",
    "EXECUTE",
    "FETCH",
    "DECLARE",
    "TRUNCATE",
    "MERGE",
    "REPLACE",
    "GRANT",
    "REVOKE",
    "UNION",
    "COUNT(",
    "VALUES",
    "TABLE",
    "INTO",
    "SET",
    "GROUP BY",
    "ORDER BY",
    "HAVING",
    "LIMIT",
    "OFFSET",
    "RETURNING",
    "ILIKE",
    "LIKE",
    "INNER",
    "LEFT JOIN",
    "RIGHT JOIN",
    "OUTER JOIN",
    "CROSS JOIN",
    "ON CONFLICT",
}


@register_rule
class SqlFStringInjectionRule(Rule):
    """Detect SQL queries using f-strings — SQL injection risk (FASTT017)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT017",
            severity=Severity.ERROR,
            description="SQL f-string interpolation detected — SQL injection vector",
            recommendation="Use parameterized queries with placeholders: execute('... WHERE id = :id', {'id': id})",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.JoinedStr):
                continue

            text = self._extract_text(node)
            if self._is_sql(text):
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.ERROR,
                        file_path=file_path,
                        rule=self.definition.id,
                        message="f-string SQL query detected — use parameterized queries instead",
                        line=node.lineno,
                        column=node.col_offset,
                        help=self.definition.recommendation,
                    )
                )

        return diagnostics

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, ast.JoinedStr):
                continue

            text = self._extract_text(node)
            if self._is_sql(text):
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.ERROR,
                        file_path=file_path,
                        rule=self.definition.id,
                        message="f-string SQL query detected — use parameterized queries instead",
                        line=node.lineno,
                        column=node.col_offset,
                        help=self.definition.recommendation,
                    )
                )

        return diagnostics

    def check_function(self, func_node, file_path):
        return []

    def _extract_text(self, node: ast.JoinedStr) -> str:
        """Extract plain text parts from an f-string."""
        parts = []
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                parts.append(part.value)
        return " ".join(parts)

    def _is_sql(self, text: str) -> bool:
        """Check if text contains SQL keywords."""
        upper = text.upper()
        return any(kw in upper for kw in SQL_KEYWORDS)
