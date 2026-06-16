import ast

from fastapi_doctor.rules.base import (
    Rule,
    register_rule,
    is_fastapi_endpoint,
    resolve_call_name,
    collect_threadpool_wrappers,
    is_inside_wrapper,
)
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity


@register_rule
class BlockingFileIORule(Rule):
    """Detect blocking open() calls inside async endpoints (FASTT005)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT005",
            severity=Severity.ERROR,
            description="open() (blocking file IO) inside async endpoint without anyio.open_file or asyncio.to_thread",
            recommendation="Use anyio.open_file() or aiofiles.open() for async file IO, or wrap open() in asyncio.to_thread()",
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
        diagnostics = []
        wrappers = collect_threadpool_wrappers(func_node)

        decorator_descendants = self._collect_decorator_descendants(func_node)
        awaited_descendants = self._collect_awaited_descendants(func_node)
        inner_func_descendants = self._collect_inner_func_descendants(func_node)

        for child in ast.walk(func_node):
            if not isinstance(child, ast.Call):
                continue
            if (
                child in decorator_descendants
                or child in awaited_descendants
                or child in inner_func_descendants
            ):
                continue

            name = resolve_call_name(child)
            if name != "open":
                continue
            if is_inside_wrapper(child, wrappers):
                continue

            diagnostics.append(
                Diagnostic(
                    severity=self.definition.severity,
                    file_path=file_path,
                    rule=self.definition.id,
                    message=f"blocking open() call inside async context '{func_node.name}' — use anyio.open_file() or asyncio.to_thread()",
                    line=child.lineno,
                    column=child.col_offset,
                    help=self.definition.recommendation,
                )
            )

        return diagnostics

    def _collect_decorator_descendants(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> set[ast.AST]:
        descendants: set[ast.AST] = set()
        for decorator in func_node.decorator_list:
            for desc in ast.walk(decorator):
                descendants.add(desc)
        return descendants

    def _collect_awaited_descendants(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> set[ast.AST]:
        descendants: set[ast.AST] = set()
        for node in ast.walk(func_node):
            if isinstance(node, ast.Await):
                for desc in ast.walk(node):
                    descendants.add(desc)
        return descendants

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
