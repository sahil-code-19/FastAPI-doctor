import ast

from fastapi_doctor.rules.base import (
    Rule,
    register_rule,
    is_fastapi_endpoint,
    get_call_sig,
    collect_threadpool_wrappers,
    is_inside_wrapper,
)
from fastapi_doctor.models import Diagnostic, RuleDefinition, Severity

BLOCKING_CALLS = {
    ("requests", "get"),
    ("requests", "post"),
    ("requests", "put"),
    ("requests", "patch"),
    ("requests", "delete"),
    ("requests", "head"),
    ("requests", "request"),
    ("requests", "Session"),
    ("urllib.request", "urlopen"),
    ("time", "sleep"),
    ("httpx", "get"),
    ("httpx", "post"),
    ("httpx", "put"),
    ("httpx", "delete"),
    ("httpx", "Client"),
}


@register_rule
class SyncBlockingIORule(Rule):
    """Detect synchronous blocking IO in async FastAPI endpoints (FASTT001)."""

    @property
    def definition(self) -> RuleDefinition:
        return RuleDefinition(
            id="fastapi-doctor/FASTT001",
            severity=Severity.ERROR,
            description="async def endpoint calling synchronous blocking IO (requests.get, urllib, time.sleep, sync httpx) without run_in_threadpool",
            recommendation="Wrap blocking IO in asyncio.to_thread() or use async alternatives (httpx.AsyncClient, asyncio.sleep, etc.)",
        )

    def check(self, tree: ast.Module, file_path: str, source: str) -> list[Diagnostic]:
        diagnostics = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.AsyncFunctionDef):
                continue

            method_name = is_fastapi_endpoint(node)
            if method_name is None:
                continue

            wrappers = collect_threadpool_wrappers(node)

            for child in ast.walk(node):
                if not isinstance(child, ast.Call):
                    continue

                call_sig = get_call_sig(child)
                if call_sig is None:
                    continue

                if call_sig in BLOCKING_CALLS:
                    if not is_inside_wrapper(child, wrappers):
                        diagnostics.append(
                            Diagnostic(
                                severity=self.definition.severity,
                                file_path=file_path,
                                rule=self.definition.id,
                                message=f"Blocking call '{call_sig[0]}.{call_sig[1]}()' inside async endpoint '{node.name}' without asyncio.to_thread()",
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

            method_name = is_fastapi_endpoint(node)
            if method_name is None:
                continue

            wrappers = collect_threadpool_wrappers(node)

            for child in ast.walk(node):
                if not isinstance(child, ast.Call):
                    continue

                call_sig = get_call_sig(child)
                if call_sig is None:
                    continue

                if call_sig in BLOCKING_CALLS:
                    if not is_inside_wrapper(child, wrappers):
                        diagnostics.append(
                            Diagnostic(
                                severity=self.definition.severity,
                                file_path=file_path,
                                rule=self.definition.id,
                                message=f"Blocking call '{call_sig[0]}.{call_sig[1]}()' inside async endpoint '{node.name}' without asyncio.to_thread()",
                                line=child.lineno,
                                column=child.col_offset,
                                help=self.definition.recommendation,
                            )
                        )

        return diagnostics
