import tomllib
from pathlib import Path
from pathspec import PathSpec


def build_file_ignore_spec(scan_root: Path) -> PathSpec:
    """Build a combined PathSpec from all file-level ignore sources."""
    patterns: list[str] = []
    current = scan_root.resolve()

    while True:
        patterns.extend(_load_gitignore_patterns(current))
        patterns.extend(_load_ruff_exclude_patterns(current))
        patterns.extend(_load_gitattributes_vendored_patterns(current))

        if (current / ".git").exists():
            break

        parent = current.parent
        if parent == current:
            break
        current = parent

    return PathSpec.from_lines("gitignore", patterns)


def should_skip_file(file_path: Path, scan_root: Path, spec: PathSpec) -> bool:
    """Check if a file should be skipped based on the ignore spec."""
    try:
        rel = file_path.resolve().relative_to(scan_root.resolve())
    except ValueError:
        return False

    rel_str = str(rel).replace("\\", "/")
    if file_path.is_dir():
        rel_str += "/"
    return spec.match_file(rel_str)


# ── .gitignore ────────────────────────────────────────────────────────────────


def _load_gitignore_patterns(directory: Path) -> list[str]:
    gitignore = directory / ".gitignore"
    if not gitignore.is_file():
        return []
    try:
        return gitignore.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []


# ── ruff.toml /.ruff.toml exclude ────────────────────────────────────────────


def _load_ruff_exclude_patterns(directory: Path) -> list[str]:
    for name in ("ruff.toml", ".ruff.toml", "pyproject.toml"):
        ruff_config = directory / name
        if not ruff_config.is_file():
            continue
        try:
            with open(ruff_config, "rb") as f:
                data = tomllib.load(f)
        except (tomllib.TOMLDecodeError, OSError):
            continue

        patterns = _extract_ruff_exclude(data)
        if patterns:
            return patterns
    return []


def _extract_ruff_exclude(data: dict) -> list[str]:
    """Extract exclude patterns from ruff config (supports both .ruff.toml and pyproject.toml)."""

    def _safe(patterns) -> list[str]:
        if (
            isinstance(patterns, list)
            and patterns
            and all(isinstance(e, str) for e in patterns)
        ):
            return patterns
        return []

    # .ruff.toml: top-level exclude = [...]
    result = _safe(data.get("exclude", []))
    if result:
        return result

    # .ruff.toml: [lint] exclude = [...]
    lint = data.get("lint", {})
    if isinstance(lint, dict):
        result = _safe(lint.get("exclude", []))
        if result:
            return result

    # pyproject.toml: [tool.ruff] exclude = [...]
    ruff = data.get("tool", {}).get("ruff", {})
    result = _safe(ruff.get("exclude", []))
    if result:
        return result

    # pyproject.toml: [tool.ruff.lint] exclude = [...]
    ruff_lint = data.get("tool", {}).get("ruff", {}).get("lint", {})
    result = _safe(ruff_lint.get("exclude", []))
    if result:
        return result

    return []


# ── .gitattributes linguist-vendored / linguist-generated ─────────────────────


def _load_gitattributes_vendored_patterns(directory: Path) -> list[str]:
    """Extract file patterns marked as linguist-vendored or linguist-generated."""
    gitattributes = directory / ".gitattributes"
    if not gitattributes.is_file():
        return []

    patterns = []
    try:
        for line in gitattributes.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "linguist-vendored" in stripped or "linguist-generated" in stripped:
                # Format: "path/pattern  linguist-vendored"
                parts = stripped.split()
                if parts:
                    patterns.append(parts[0])
    except OSError:
        pass

    return patterns
