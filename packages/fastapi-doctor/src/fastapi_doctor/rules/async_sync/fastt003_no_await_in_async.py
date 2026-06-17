import ast

from fastapi_doctor.rules.base import Rule, register_rule, is_fastapi_endpoint
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


_ASYNC_TYPE_PATTERNS = {
    "AsyncSession",
    "AsyncGenerator",
    "AsyncIterator",
    "AsyncContextManager",
}
_ASYNC_PREFIXES = ("async_", "Async")


@register_rule
class NoAwaitInAsyncRule(Rule):
    """Detect async def endpoints that have no await/async-for/async-with (FASTT003).

    Two severity levels:
    - WARNING: has async-capable params (e.g. db: AsyncSession) but no await — developer likely intends to add awaits
    - ERROR: no async-capable params AND no await — likely mistakenly async or forgotten await
    """

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT003",
            severity=Severity.ERROR,
            description="async def endpoint has no await, async for, or async with",
            recommendation="Remove async if the function is purely CPU-bound, or add missing await on async calls",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            diagnostics.extend(self._check_single(node, file_path))
        return diagnostics

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            if is_fastapi_endpoint(node) is None:
                continue
            diagnostics.extend(self._check_single(node, file_path))
        return diagnostics

    def check_function(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: str
    ) -> list[Diagnostic]:
        if not isinstance(func_node, ast.AsyncFunctionDef):
            return []
        return self._check_single(func_node, file_path)

    def _check_single(
        self, func_node: ast.AsyncFunctionDef, file_path: str
    ) -> list[Diagnostic]:
        if self._has_async_constructs(func_node):
            return []

        has_async_params = self._has_async_capable_params(func_node)
        severity = Severity.WARNING if has_async_params else Severity.ERROR

        reason = (
            "has async-capable parameters but no await — developer may intend to add awaits later"
            if has_async_params
            else "has no await and no async-capable parameters — likely mistakenly async or missing await"
        )

        return [
            Diagnostic(
                severity=severity,
                file_path=file_path,
                rule=self.definition.id,
                message=f"async endpoint '{func_node.name}' {reason}",
                line=func_node.lineno,
                column=func_node.col_offset,
                help=self.definition.recommendation,
            )
        ]

    def _has_async_constructs(self, func_node: ast.AsyncFunctionDef) -> bool:
        inner_funcs: set[ast.AST] = set()
        for node in ast.walk(func_node):
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node is not func_node
            ):
                for desc in ast.walk(node):
                    inner_funcs.add(desc)

        for node in ast.walk(func_node):
            if node in inner_funcs:
                continue
            if isinstance(node, (ast.Await, ast.AsyncFor, ast.AsyncWith)):
                return True

        return False

    def _has_async_capable_params(self, func_node: ast.AsyncFunctionDef) -> bool:
        for arg in func_node.args.args:
            annotation = arg.annotation
            if annotation is None:
                continue
            type_name = self._extract_type_name(annotation)
            if type_name is None:
                continue
            if type_name in _ASYNC_TYPE_PATTERNS:
                return True
            if type_name.startswith(_ASYNC_PREFIXES):
                return True

        defaults = func_node.args.defaults
        num_args = len(func_node.args.args)
        num_defaults = len(defaults)
        offset = num_args - num_defaults
        for i, default in enumerate(defaults):
            if default is not None and self._depends_on_async(default):
                return True

        return False

    def _extract_type_name(self, annotation: ast.expr) -> str | None:
        if isinstance(annotation, ast.Name):
            return annotation.id
        if isinstance(annotation, ast.Attribute):
            return annotation.attr
        if isinstance(annotation, ast.Subscript):
            return self._extract_type_name(annotation.value)
        return None

    def _depends_on_async(self, default: ast.expr) -> bool:
        if not isinstance(default, ast.Call):
            return False
        if not isinstance(default.func, ast.Name):
            return False
        if default.func.id != "Depends":
            return False
        if not default.args:
            return False
        dep = default.args[0]
        dep_name = self._extract_dep_name(dep)
        if dep_name and "async" in dep_name.lower():
            return True
        return False

    def _extract_dep_name(self, dep: ast.expr) -> str | None:
        if isinstance(dep, ast.Name):
            return dep.id
        if isinstance(dep, ast.Attribute):
            return dep.attr
        return None
