import ast
from abc import ABC, abstractmethod

from ..models import Diagnostic, RuleDefinition


class Rule(ABC):
    @property
    @abstractmethod
    def definition(self) -> RuleDefinition: ...

    @abstractmethod
    def check(
        self, tree: ast.Module, file_path: str, source: str
    ) -> list[Diagnostic]: ...

    def check_function(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: str
    ) -> list[Diagnostic]:
        """Check a single function body. Override for rules that support import tracing."""
        return []


_RULES: list[type[Rule]] = []


def register_rule(cls: type[Rule]) -> type[Rule]:
    """Decorator to register a rule class."""
    _RULES.append(cls)
    return cls


def get_all_rules() -> list[type[Rule]]:
    """Return all registered rules."""
    return _RULES.copy()


FASTAPI_DECORATOR_METHODS = {
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "head",
    "options",
}


def is_fastapi_endpoint(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str | None:
    """Return the HTTP method name if the function is a FastAPI endpoint, else None."""
    for decorator in func_node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        if not isinstance(decorator.func, ast.Attribute):
            continue
        if decorator.func.attr in FASTAPI_DECORATOR_METHODS:
            return decorator.func.attr
    return None


def get_call_sig(node: ast.Call) -> tuple[str, str] | None:
    """Extract (module, function) tuple from an attribute call like requests.get()."""
    if isinstance(node.func, ast.Attribute):
        if isinstance(node.func.value, ast.Name):
            return (node.func.value.id, node.func.attr)
    return None


def resolve_call_name(node: ast.Call) -> str | None:
    """Resolve a call to a dotted name string like 'asyncio.to_thread'."""
    if isinstance(node.func, ast.Attribute):
        parts = []
        current: ast.expr = node.func
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
            return ".".join(reversed(parts))
    elif isinstance(node.func, ast.Name):
        return node.func.id
    return None


THREADPOOL_CALL_NAMES = {
    "asyncio.to_thread",
    "fastapi.concurrency.run_in_threadpool",
    "run_in_threadpool",
}


def collect_threadpool_wrappers(func_node: ast.AST) -> list[ast.Call]:
    """Find all asyncio.to_thread() and run_in_threadpool() calls in a function."""
    wrappers = []
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            name = resolve_call_name(node)
            if name in THREADPOOL_CALL_NAMES:
                wrappers.append(node)
    return wrappers


def is_inside_wrapper(call_node: ast.Call, wrappers: list[ast.Call]) -> bool:
    """Check if call_node is a descendant of any wrapper call."""
    for wrapper in wrappers:
        for desc in ast.walk(wrapper):
            if desc is call_node:
                return True
    return False


def build_import_map(tree: ast.Module) -> dict[str, str]:
    """Build a map of imported name -> full module path from `from X import Y` statements.

    Handles both absolute and relative imports:
        from app.crud.users import create_user  ->  'create_user' -> 'app.crud.users'
        from ..crud.users import get_user       ->  'get_user' -> '..crud.users'
    """
    import_map: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue

            dots = "." * node.level
            full_module = dots + node.module if node.level > 0 else node.module

            for alias in node.names:
                import_map[alias.name] = full_module
    return import_map


def resolve_module_path(
    module_name: str, project_root: str, source_file: str = ""
) -> str | None:
    """Convert a module path or relative import to a file path.

    Handles:
        'app.crud.company'  -> '{project_root}/app/crud/company.py'
        '..crud.users'      -> resolved relative to source_file's directory
    """
    from pathlib import Path

    if module_name.startswith(".") and source_file:
        source_dir = Path(source_file).parent

        dot_count = 0
        for ch in module_name:
            if ch == ".":
                dot_count += 1
            else:
                break

        levels_up = dot_count - 1
        for _ in range(levels_up):
            source_dir = source_dir.parent

        remaining = module_name[dot_count:]
        resolved = source_dir / (remaining.replace(".", "/") + ".py")
        resolved = resolved.resolve()
        if resolved.exists():
            return str(resolved)
        return None

    parts = module_name.split(".")
    candidate = Path(project_root, *parts).with_suffix(".py")
    if candidate.exists():
        return str(candidate)
    return None
