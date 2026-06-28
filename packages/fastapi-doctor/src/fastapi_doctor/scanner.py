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
    vulture_flag: bool | None = None,
) -> ScanResult:
    start_time = time.perf_counter()
    all_diagnostics: list[Diagnostic] = []
    rule_instances = [rule_cls() for rule_cls in get_all_rules()]

    # Load and apply project config (suppressions, ignore patterns)
    config = load_config(directory)
    if audit:
        config.respectInlineDisables = False
    ruff_enabled = ruff_flag if ruff_flag is not None else config.ruff
    vulture_enabled = vulture_flag if vulture_flag is not None else config.vulture

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

    # Parallel: import trace + ruff + vulture
    with ThreadPoolExecutor(max_workers=3) as secondary:
        trace_future = secondary.submit(
            _run_trace_pass, parsed_files, directory, rule_instances
        )
        ruff_future = (
            secondary.submit(_run_ruff, file_list, directory) if ruff_enabled else None
        )
        vulture_future = (
            secondary.submit(_run_vulture, file_list, directory)
            if vulture_enabled
            else None
        )

        if trace_future:
            all_diagnostics.extend(trace_future.result())
        if ruff_future:
            all_diagnostics.extend(ruff_future.result())
        if vulture_future:
            all_diagnostics.extend(vulture_future.result())

    # Circular import detection (FASTT023 — cross-file check)
    circular_diags = _check_circular_imports(parsed_files, directory)
    all_diagnostics.extend(circular_diags)

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


def _run_trace_pass(parsed_files, directory, rule_instances):
    trees_only = {path: tree for path, (tree, _) in parsed_files.items()}
    return trace_and_check(trees_only, str(directory), rule_instances)


def _run_ruff(files, directory):
    from .ruff_integration import run_ruff_check

    return run_ruff_check(files, directory)


def _run_vulture(files, directory):
    from .vulture_integration import run_vulture_check

    return run_vulture_check(files, directory)


def _check_circular_imports(
    parsed_files: dict[str, tuple[ast.Module, str]], directory: Path
) -> list[Diagnostic]:
    """Detect circular imports between files (FASTT023)."""
    from .models import Diagnostic, Severity

    imports_by_file: dict[str, set[str]] = {}
    for file_path, (tree, _) in parsed_files.items():
        imports = _resolve_relative_imports(tree, file_path, parsed_files)
        if imports:
            imports_by_file[file_path] = imports

    diagnostics = []
    seen_pairs: set[tuple[str, str]] = set()

    for file_a, imports_from_a in imports_by_file.items():
        for file_b in imports_from_a:
            if file_b not in imports_by_file:
                continue
            pair = tuple(sorted([file_a, file_b]))
            if pair in seen_pairs:
                continue
            if file_a in imports_by_file.get(file_b, set()):
                seen_pairs.add(pair)
                a_rel = _rel_path(file_a, directory)
                b_rel = _rel_path(file_b, directory)
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.ERROR,
                        file_path=a_rel,
                        rule="fastapi-doctor/FASTT023",
                        message=f"circular import detected: '{a_rel}' ↔ '{b_rel}' (each imports from the other)",
                        line=1,
                        column=0,
                        help="Extract shared symbols to a separate module to break the cycle",
                    )
                )

    return diagnostics


def _resolve_relative_imports(
    tree: ast.Module, file_path: str, parsed_files: dict[str, tuple[ast.Module, str]]
) -> set[str]:
    """Resolve relative imports in a file to absolute file paths."""
    resolved = set()
    source_dir = Path(file_path).parent.resolve()

    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level == 0 or node.module is None:
            continue
        module = "." * node.level + node.module
        resolved_path = _resolve_module_path(file_path, module, parsed_files)
        if resolved_path:
            resolved.add(resolved_path)
    return resolved


def _resolve_module_path(
    file_path: str, module: str, parsed_files: dict[str, tuple[ast.Module, str]]
) -> str | None:
    """Resolve a relative import like '.module' to a file path in parsed_files."""
    source_dir = Path(file_path).parent.resolve()
    resolved_file_paths: dict[str, str] = {}
    for key in parsed_files:
        try:
            resolved_file_paths[str(Path(key).resolve())] = key
        except OSError:
            pass

    # Count leading dots for level
    dots = 0
    for ch in module:
        if ch == ".":
            dots += 1
        else:
            break

    if dots == 0:
        return None

    # Go up for each dot beyond the first (first dot = current package)
    current = source_dir
    for _ in range(dots - 1):
        current = current.parent

    module_name = module[dots:]  # content after dots
    parts = [p for p in module_name.split(".") if p]

    if parts:
        rel = current / "/".join(parts)
    else:
        rel = current

    py_file = str(rel.with_suffix(".py").resolve())
    if py_file in resolved_file_paths:
        target = resolved_file_paths[py_file]
        if target != file_path:
            return target

    init_file = str((rel / "__init__.py").resolve())
    if init_file in resolved_file_paths:
        target = resolved_file_paths[init_file]
        if target != file_path:
            return target

    return None


def _rel_path(absolute: str, directory: Path) -> str:
    try:
        return str(Path(absolute).relative_to(directory))
    except ValueError:
        return absolute
