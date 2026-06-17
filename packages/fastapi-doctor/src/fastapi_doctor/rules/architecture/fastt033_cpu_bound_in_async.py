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

CPU_BOUND_CALLS = {
    "PIL.Image.open",
    "Image.open",
    "cv2.imread",
    "cv2.imwrite",
    "cv2.cvtColor",
    "hashlib.sha256",
    "hashlib.md5",
}


@register_rule
class CpuBoundInAsyncRule(Rule):
    """Detect known CPU-bound operations inside async endpoints without asyncio.to_thread (FASTT033)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT033",
            severity=Severity.WARNING,
            description="CPU-bound operation inside async endpoint without asyncio.to_thread() — can block the event loop",
            recommendation="Wrap CPU-bound calls in `await asyncio.to_thread(cpu_bound_func, ...)` to avoid blocking the event loop",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            if is_fastapi_endpoint(node) is None:
                continue

            wrappers = collect_threadpool_wrappers(node)

            for child in ast.walk(node):
                if not isinstance(child, ast.Call):
                    continue
                call_name = resolve_call_name(child)
                if call_name is None:
                    continue
                if call_name not in CPU_BOUND_CALLS:
                    continue
                if is_inside_wrapper(child, wrappers):
                    continue

                diagnostics.append(
                    Diagnostic(
                        severity=self.definition.severity,
                        file_path=file_path,
                        rule=self.definition.id,
                        message=f"CPU-bound call '{call_name}()' inside async endpoint '{node.name}' without asyncio.to_thread()",
                        line=child.lineno,
                        column=child.col_offset,
                        help=self.definition.recommendation,
                    )
                )
        return diagnostics

    def check_from_nodes(self, nodes, tree, file_path, source):
        diagnostics = []
        for node in nodes:
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            if is_fastapi_endpoint(node) is None:
                continue

            wrappers = collect_threadpool_wrappers(node)

            for child in ast.walk(node):
                if not isinstance(child, ast.Call):
                    continue
                call_name = resolve_call_name(child)
                if call_name is None:
                    continue
                if call_name not in CPU_BOUND_CALLS:
                    continue
                if is_inside_wrapper(child, wrappers):
                    continue

                diagnostics.append(
                    Diagnostic(
                        severity=self.definition.severity,
                        file_path=file_path,
                        rule=self.definition.id,
                        message=f"CPU-bound call '{call_name}()' inside async endpoint '{node.name}' without asyncio.to_thread()",
                        line=child.lineno,
                        column=child.col_offset,
                        help=self.definition.recommendation,
                    )
                )
        return diagnostics

    def check_function(self, func_node, file_path):
        return []
