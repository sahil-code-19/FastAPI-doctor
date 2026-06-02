import ast

from fastapi_doctor.rules.base import Rule, register_rule, is_fastapi_endpoint
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity

ORM_METHODS = {"query", "execute", "get", "refresh"}
ORM_RESULT_METHODS = {
    "first",
    "all",
    "one",
    "get",
    "scalars",
    "fetchall",
    "fetchone",
    "scalar",
}


@register_rule
class ReturnSqlalchemyBaseClass(Rule):
    """Detect endpoints returning ORM model instances instead of Pydantic schemas (FASTT010)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT010",
            severity=Severity.ERROR,
            description="Route handler returning ORM model instance directly (SQLAlchemy Base subclass) instead of Pydantic schema — data leakage risk",
            recommendation="Convert to Pydantic schema with model_validate() before returning, e.g. return UserSchema.model_validate(user)",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            diagnostics.extend(self._check_single(node, file_path))
        return diagnostics

    def check_function(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: str
    ) -> list[Diagnostic]:
        if not isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return []
        return self._check_single(func_node, file_path)

    def _check_single(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: str
    ) -> list[Diagnostic]:
        diagnostics = []

        inner_func_descendants = self._collect_inner_func_descendants(func_node)
        decorator_descendants = self._collect_decorator_descendants(func_node)

        db_sourced_vars = self._collect_db_sourced_vars(
            func_node, inner_func_descendants
        )

        for node in ast.walk(func_node):
            if node in inner_func_descendants or node in decorator_descendants:
                continue
            if not isinstance(node, ast.Return):
                continue
            if node.value is None:
                continue

            if self._is_returning_db_value(node.value, db_sourced_vars):
                diagnostics.append(
                    Diagnostic(
                        severity=self.definition.severity,
                        file_path=file_path,
                        rule=self.definition.id,
                        message=f"endpoint '{func_node.name}' returns ORM model directly — data leakage risk",
                        line=node.lineno,
                        column=node.col_offset,
                        help=self.definition.recommendation,
                    )
                )

        return diagnostics

    def _is_returning_db_value(
        self, value: ast.expr, db_sourced_vars: set[str]
    ) -> bool:
        """Check if the return value directly is/came from a DB call."""
        if isinstance(value, ast.Name) and value.id in db_sourced_vars:
            return True
        if isinstance(value, ast.Call):
            return self._is_db_call(value)
        return False

    def _is_db_call(self, call_node: ast.Call) -> bool:
        """Check if a call chain traces back to an ORM method."""
        if not isinstance(call_node.func, ast.Attribute):
            return False
        attr = call_node.func.attr
        if attr in ORM_METHODS:
            return True
        if attr in ORM_RESULT_METHODS:
            return self._has_db_method_in_chain(call_node)
        return False

    def _has_db_method_in_chain(self, call_node: ast.Call) -> bool:
        """Walk the call chain to find a root ORM method like query/execute/get."""
        if (
            isinstance(call_node.func, ast.Attribute)
            and call_node.func.attr in ORM_METHODS
        ):
            return True
        if isinstance(call_node.func, ast.Attribute):
            base = call_node.func.value
            if isinstance(base, ast.Call):
                return self._has_db_method_in_chain(base)
        return False

    def _collect_db_sourced_vars(
        self,
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
        inner_func_descendants: set[ast.AST],
    ) -> set[str]:
        """Find variables assigned from DB calls like `user = db.query(User).first()`."""
        db_sourced: set[str] = set()
        for node in ast.walk(func_node):
            if node in inner_func_descendants:
                continue
            if not isinstance(node, ast.Assign):
                continue
            if not self._expr_contains_db_call(node.value):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    db_sourced.add(target.id)
                elif isinstance(target, ast.Tuple):
                    for elt in target.elts:
                        if isinstance(elt, ast.Name):
                            db_sourced.add(elt.id)
        return db_sourced

    def _expr_contains_db_call(self, expr: ast.expr) -> bool:
        """Check if an expression contains a DB method call (used for tracking assignments)."""
        for node in ast.walk(expr):
            if isinstance(node, ast.Call):
                if self._is_db_call(node):
                    return True
        return False

    def _collect_inner_func_descendants(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> set[ast.AST]:
        descendants: set[ast.AST] = set()
        for node in ast.walk(func_node):
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node is not func_node
            ):
                for desc in ast.walk(node):
                    descendants.add(desc)
        return descendants

    def _collect_decorator_descendants(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> set[ast.AST]:
        descendants: set[ast.AST] = set()
        for decorator in func_node.decorator_list:
            for desc in ast.walk(decorator):
                descendants.add(desc)
        return descendants
