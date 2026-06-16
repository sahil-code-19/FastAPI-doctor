import threading
import ast
import time
import os

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from .models import Diagnostic, ScanResult
from .rules.base import (
    build_import_map,
    get_all_rules,
    is_fastapi_endpoint,
    resolve_module_path,
)
from . import rules  # Import rules module to trigger @register_rule decorators
from .config import load_config, should_skip_file, is_rule_suppressed
from .inline_suppression import parse_inline_suppressions, is_diagnostic_suppressed
from .file_ignore import build_file_ignore_spec, should_skip_file as should_skip_by_spec

SKIP_DIRS = [
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "node_modules",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".tox",
]

PYTHON_EXTENSIONS = {".py"}


def find_python_files(directory: Path) -> list[Path]:
    """Walk directory, skipping pruned dirs before recursion for performance."""
    files = []
    for root, dirs, filenames in os.walk(str(directory)):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(".py"):
                files.append(Path(root) / name)
    return sorted(files)


def parse_file(file_path: Path) -> ast.Module | None:
    try:
        source = file_path.read_text(encoding="utf-8")
        return ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return None


def build_function_catalog(
    parsed_files: dict[str, ast.Module],
) -> dict[str, dict[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    """Build catalog: file_path -> {function_name -> AST node}."""
    catalog: dict[str, dict[str, ast.FunctionDef | ast.AsyncFunctionDef]] = {}
    for file_path, tree in parsed_files.items():
        functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions[node.name] = node
        catalog[file_path] = functions
    return catalog


def _check_single_file(file_path_str, tree, source, rule_instances, directory, config):
    """Runs in a worker thread — one file, all rules."""
    nodes = list(ast.walk(tree))  # pre-walk once, share across all rules
    file_diagnostics = []
    for rule in rule_instances:
        if is_rule_suppressed(rule.definition.id, file_path_str, directory, config):
            continue
        diagnostics = rule.check_from_nodes(nodes, tree, file_path_str, source)
        file_diagnostics.extend(diagnostics)
    if config.respectInlineDisables:
        suppressions = parse_inline_suppressions(source)
        file_diagnostics = [
            d for d in file_diagnostics if not is_diagnostic_suppressed(d, suppressions)
        ]
        from .near_miss_hints import generate_near_miss_hints

        hints = generate_near_miss_hints(file_diagnostics, source, file_path_str)
        file_diagnostics.extend(hints)
    return file_diagnostics


def _resolve_callee_name(node: ast.Call) -> str | None:
    """Get the name of the directly-called function, e.g. 'create_item' from create_item(db, data)."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    return None


def _resolve_callee_module_func(node: ast.Call) -> tuple[str, str] | None:
    """Get (module_alias, function_name) from module.func() calls like crud.create_job()."""
    if isinstance(node.func, ast.Attribute):
        if isinstance(node.func.value, ast.Name):
            return (node.func.value.id, node.func.attr)
    return None


def trace_and_check(
    parsed_files: dict[str, ast.Module],
    scan_directory_path: str,
    all_rules: list,
) -> list[Diagnostic]:
    """Second pass: trace calls from endpoints into imported CRUD functions."""
    extra_diagnostics: list[Diagnostic] = []

    catalog = build_function_catalog(parsed_files)

    for file_path, tree in parsed_files.items():
        import_map = build_import_map(tree)

        for node in ast.walk(tree):
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue

            method_name = is_fastapi_endpoint(node)
            if method_name is None:
                continue

            for child in ast.walk(node):
                if not isinstance(child, ast.Call):
                    continue

                # Case 1: Direct import: from crud.users import create_user -> create_user(db)
                callee_name = _resolve_callee_name(child)
                module_ref = import_map.get(callee_name or "")

                # Case 2: Module import: from crud import users -> users.create_user(db)
                mod_func = _resolve_callee_module_func(child)
                if not module_ref and mod_func:
                    module_alias, func_name = mod_func
                    module_ref = import_map.get(module_alias)
                    if module_ref and callee_name is None:
                        callee_name = func_name

                if module_ref is None or callee_name is None:
                    continue

                resolved_crud_path = resolve_module_path(
                    module_ref, scan_directory_path, file_path
                )
                if resolved_crud_path is None or resolved_crud_path not in catalog:
                    continue

                crud_functions = catalog[resolved_crud_path]
                if callee_name not in crud_functions:
                    continue

                crud_func_node = crud_functions[callee_name]

                for rule in all_rules:
                    extra = rule.check_function(crud_func_node, resolved_crud_path)
                    extra_diagnostics.extend(extra)

    return extra_diagnostics


def scan_directory(
    directory: Path,
    files: list[Path] | None = None,
    audit: bool = False,
    mode: str = "full",
    ruff_flag: bool | None = None,
) -> ScanResult:
    start_time = time.perf_counter()
    all_diagnostics: list[Diagnostic] = []
    rule_instances = [rule_cls() for rule_cls in get_all_rules()]

    # Load and apply project config (suppressions, ignore patterns)
    config = load_config(directory)
    if audit:
        config.respectInlineDisables = False
    ruff_enabled = ruff_flag if ruff_flag is not None else config.ruff

    if files is not None:
        file_list = files
    else:
        file_list = find_python_files(directory)

    # Apply config-level ignore.files patterns
    file_list = [f for f in file_list if not should_skip_file(f, directory, config)]

    # Apply file-level ignores (.gitignore, .ruff.toml, .prettierignore, .gitattributes)
    file_ignore_spec = build_file_ignore_spec(directory)
    file_list = [
        f for f in file_list if not should_skip_by_spec(f, directory, file_ignore_spec)
    ]

    # Cap workers at min(cpu_count, file_count, 8) for optimal throughput
    workers = max(min(os.cpu_count() or 1, len(file_list), 8), 1)

    # Parse all files once, store ASTs for both main scan and trace pass
    parsed_files: dict[str, tuple[ast.Module, str]] = {}
    for file_path in file_list:
        source = file_path.read_text(encoding="utf-8")
        tree = parse_file(file_path)
        if tree is not None:
            parsed_files[str(file_path)] = (tree, source)

    # Main scan pass
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                _check_single_file, fp, tree, source, rule_instances, directory, config
            ): fp
            for fp, (tree, source) in parsed_files.items()
        }
        for future in as_completed(futures):
            all_diagnostics.extend(future.result())

    # Import trace pass
    trees_only = {path: tree for path, (tree, _) in parsed_files.items()}
    traced_diagnostics = trace_and_check(
        trees_only,
        str(directory),
        rule_instances,
    )
    all_diagnostics.extend(traced_diagnostics)

    # Ruff integration — run ruff check on same files
    if ruff_enabled:
        from .ruff_integration import run_ruff_check

        ruff_diags = run_ruff_check(file_list, directory)
        all_diagnostics.extend(ruff_diags)

    # Apply suppression to traced diagnostics as well
    all_diagnostics = [
        d
        for d in all_diagnostics
        if not is_rule_suppressed(d.rule, d.file_path, directory, config)
    ]

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    return ScanResult(
        diagnostics=all_diagnostics,
        files_scanned=len(file_list),
        elapsed_ms=elapsed_ms,
        mode=mode,
    )
