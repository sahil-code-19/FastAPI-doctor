import ast

from fastapi_doctor.rules.base import Rule, register_rule, is_fastapi_endpoint
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class UnboundedQueryRule(Rule):
    """Detect `db.query(Model).all()` without pagination inside route handlers (FASTT035)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT035",
            severity=Severity.WARNING,
            description="Unbounded database query (.all()/.scalars().all()) without limit/offset/pagination — can return excessive rows",
            recommendation="Add .limit() and .offset() for pagination, or use .paginate() if available",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue

            # Track DB-result variables for SA 2.0 execute().scalars().all() patterns
            db_result_vars = self._track_db_result_vars(node)

            for child in ast.walk(node):
                if (
                    isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and child is not node
                ):
                    continue
                if not isinstance(child, ast.Call):
                    continue
                if not self._is_unbounded_all_child(child, db_result_vars):
                    continue
                diagnostics.append(
                    Diagnostic(
                        severity=self.definition.severity,
                        file_path=file_path,
                        rule=self.definition.id,
                        message="unbounded DB query with .all() — add .limit()/.offset() for pagination",
                        line=child.lineno,
                        column=child.col_offset,
                        help=self.definition.recommendation,
                    )
                )
        return diagnostics

    def _track_db_result_vars(self, func_node) -> dict[str, bool]:
        """Track variables assigned from db.execute() — check if the query has pagination."""
        result_vars = {}
        for node in ast.walk(func_node):
            if isinstance(node, ast.Assign):
                call_value = node.value
                if isinstance(call_value, ast.Await):
                    call_value = call_value.value
                if not isinstance(call_value, ast.Call):
                    continue
                if not isinstance(call_value.func, ast.Attribute):
                    continue
                if call_value.func.attr not in {"execute", "query"}:
                    continue

                has_pagination = self._call_or_args_have_pagination(call_value)
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        result_vars[target.id] = has_pagination
        return result_vars

    def _is_unbounded_all_child(
        self, call_node: ast.Call, db_result_vars: dict[str, bool]
    ) -> bool:
        if not isinstance(call_node.func, ast.Attribute):
            return False
        if call_node.func.attr not in {"all", "scalars"}:
            return False

        # Check if chain has query/execute root
        if self._has_query_method_in_chain(call_node):
            return True

        # Check if this is result.scalars().all() where result came from db.execute()
        if isinstance(call_node.func.value, ast.Attribute):
            base = call_node.func.value  # the .scalars() call
            if isinstance(base.value, ast.Name) and base.value.id in db_result_vars:
                return not db_result_vars[base.value.id]
        if isinstance(call_node.func.value, ast.Call):
            base = call_node.func.value
            if isinstance(base.func, ast.Attribute) and base.func.attr == "scalars":
                if (
                    isinstance(base.func.value, ast.Name)
                    and base.func.value.id in db_result_vars
                ):
                    return not db_result_vars[base.func.value.id]

        return False

    def _is_unbounded_all_call(self, call_node: ast.Call) -> bool:
        if not isinstance(call_node.func, ast.Attribute):
            return False
        if call_node.func.attr not in {"all", "scalars"}:
            return False
        return self._has_query_method_in_chain(call_node)

    def _has_query_method_in_chain(self, call_node: ast.Call) -> bool:
        if isinstance(call_node.func, ast.Attribute) and call_node.func.attr in {
            "query",
            "execute",
        }:
            return not self._call_or_args_have_pagination(call_node)
        if isinstance(call_node.func, ast.Attribute) and isinstance(
            call_node.func.value, ast.Call
        ):
            base = call_node.func.value
            chain_attr = getattr(base.func, "attr", None)
            if chain_attr in {"limit", "offset", "paginate"}:
                return False
            return self._has_query_method_in_chain(base)
        return False

    def _call_or_args_have_pagination(self, call_node: ast.Call) -> bool:
        """Check if execute()/query() call or its builder-arg has limit/offset."""
        for kw in call_node.keywords:
            if kw.arg in ("limit", "offset"):
                return True
        for arg in call_node.args:
            if isinstance(arg, ast.Call):
                if self._call_chain_has_pagination(arg):
                    return True
        return False

    def _call_chain_has_pagination(self, call_node: ast.Call) -> bool:
        """Check if a call chain (like select().where().offset().limit()) has pagination."""
        if isinstance(call_node.func, ast.Attribute) and call_node.func.attr in {
            "limit",
            "offset",
            "paginate",
        }:
            return True
        if isinstance(call_node.func, ast.Attribute) and isinstance(
            call_node.func.value, ast.Call
        ):
            return self._call_chain_has_pagination(call_node.func.value)
        return False

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if is_fastapi_endpoint(node) is None:
                continue

            db_result_vars = self._track_db_result_vars(node)

            for child in ast.walk(node):
                if (
                    isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and child is not node
                ):
                    continue
                if not isinstance(child, ast.Call):
                    continue
                if not self._is_unbounded_all_child(child, db_result_vars):
                    continue
                diagnostics.append(
                    Diagnostic(
                        severity=self.definition.severity,
                        file_path=file_path,
                        rule=self.definition.id,
                        message="unbounded DB query with .all() — add .limit()/.offset() for pagination",
                        line=child.lineno,
                        column=child.col_offset,
                        help=self.definition.recommendation,
                    )
                )
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
