import ast
import vulture
from pathlib import Path
from .models import Diagnostic, Severity

DEAD_CODE_RULES = {
    "class": "fastapi-doctor/FASTT060",
    "function": "fastapi-doctor/FASTT061",
    "method": "fastapi-doctor/FASTT061",
    "import": "fastapi-doctor/FASTT063",
    "variable": "fastapi-doctor/FASTT063",
    "property": "fastapi-doctor/FASTT060",
    "attribute": "fastapi-doctor/FASTT060",
    "parameter": "fastapi-doctor/FASTT061",
}

ALEMBIC_FUNCTIONS = {"upgrade", "downgrade"}
ALEMBIC_VARS = {"revision", "down_revision", "branch_labels", "depends_on"}
HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "options", "trace"}


def _confidence_to_severity(confidence: int) -> Severity:
    if confidence >= 90:
        return Severity.ERROR
    return Severity.WARNING


def _is_route_handler(file_path: Path, line: int, name: str) -> bool:
    """Check if a function at given line is a FastAPI route handler (decorator-registered)."""
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return False

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name != name:
            continue
        if not (node.lineno - 3 <= line <= node.end_lineno + 3):
            continue
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Attribute) and decorator.attr in HTTP_METHODS:
                return True
            if isinstance(decorator, ast.Call):
                if (
                    isinstance(decorator.func, ast.Attribute)
                    and decorator.func.attr in HTTP_METHODS
                ):
                    return True
    return False


def _is_pydantic_model(file_path: Path, line: int, name: str) -> bool:
    """Check if a class is a Pydantic BaseModel (used implicitly via type hints)."""
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return False

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if node.name != name:
            continue
        if node.lineno != line:
            continue
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "BaseModel":
                return True
            if isinstance(base, ast.Attribute) and base.attr == "BaseModel":
                return True
    return False


def _is_class_attribute(file_path: Path, line: int, name: str) -> bool:
    """Check if a variable is a class-level attribute (model field, schema, config).
    Class attributes are almost never dead code — they're used by ORMs/Pydantic."""
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return False

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if not (node.lineno <= line <= node.end_lineno + 3):
            continue
        for child in node.body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id == name:
                        return True
            if isinstance(child, ast.AnnAssign):
                if isinstance(child.target, ast.Name) and child.target.id == name:
                    return True
    return False

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(_is_model_base(b) for b in node.bases):
            continue
        if not (node.lineno <= line <= node.end_lineno + 3):
            continue
        for child in node.body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id == name:
                        return True
            if isinstance(child, ast.AnnAssign):
                if isinstance(child.target, ast.Name) and child.target.id == name:
                    return True
    return False


def _is_websocket_handler(file_path: Path, line: int, name: str) -> bool:
    """Check if function is a WebSocket route handler."""
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return False

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name != name:
            continue
        if not (node.lineno - 3 <= line <= node.end_lineno + 3):
            continue
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if (
                    isinstance(decorator.func, ast.Attribute)
                    and decorator.func.attr == "websocket"
                ):
                    return True
    return False


def _is_model_base(base: ast.expr) -> bool:
    """Check if a base class is Pydantic BaseModel or SQLAlchemy declarative Base."""
    if isinstance(base, ast.Name) and base.id in (
        "BaseModel",
        "Base",
        "DeclarativeBase",
    ):
        return True
    if isinstance(base, ast.Attribute) and base.attr in ("BaseModel", "Base"):
        return True
    if isinstance(base, ast.Call):
        if isinstance(base.func, ast.Name) and base.func.id in ("declarative_base",):
            return True
    return False


def _is_annotated_alias(file_path: Path, line: int, name: str) -> bool:
    """Check if a variable is an Annotated type alias like CurrentUser = Annotated[User, Depends(...)]."""
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return False

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if node.lineno != line:
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == name:
                if isinstance(node.value, ast.Subscript):
                    if (
                        isinstance(node.value.value, ast.Name)
                        and node.value.value.id == "Annotated"
                    ):
                        return True
    return False


def run_vulture_check(files: list[Path], scan_root: Path) -> list[Diagnostic]:
    """Run vulture dead code detection on given files, filtering false positives."""
    if not files:
        return []

    v = vulture.Vulture(verbose=False)
    try:
        v.scavenge([str(f) for f in files])
    except Exception:
        return []

    diagnostics = []
    for item in v.get_unused_code(min_confidence=60, sort_by_size=True):
        try:
            filename = Path(item.filename).relative_to(scan_root.resolve())
        except (ValueError, OSError):
            filename = Path(item.filename)

        # Skip __init__.py files (re-exports are normal)
        if filename.name == "__init__.py":
            continue

        # Filter false positives
        file_path = scan_root / filename

        if item.typ in ("function", "method"):
            if item.name in ALEMBIC_FUNCTIONS:
                continue
            if item.name == "dispatch":
                continue
            if _is_route_handler(file_path, item.first_lineno, item.name):
                continue
            if _is_websocket_handler(file_path, item.first_lineno, item.name):
                continue

        if item.typ == "class":
            if _is_pydantic_model(file_path, item.first_lineno, item.name):
                continue

        if item.typ == "variable":
            if item.name in ALEMBIC_VARS and "alembic" in str(filename):
                continue
            if _is_class_attribute(file_path, item.first_lineno, item.name):
                continue
            if _is_annotated_alias(file_path, item.first_lineno, item.name):
                continue

        rule = DEAD_CODE_RULES.get(item.typ, "fastapi-doctor/FASTT061")
        diagnostics.append(
            Diagnostic(
                file_path=str(filename),
                rule=rule,
                severity=_confidence_to_severity(item.confidence),
                message=item.message,
                line=item.first_lineno,
                column=0,
                help=f"Confidence: {item.confidence}% — consider removing or refactoring",
            )
        )

    return diagnostics
