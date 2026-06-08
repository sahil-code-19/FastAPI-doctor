import json
import tomllib

from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class OverrideConfig:
    files: list[str]
    rules: list[str] | None = None


@dataclass
class IgnoreConfig:
    rules: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    overrides: list[OverrideConfig] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class FastapiDoctorConfig:
    ignore: IgnoreConfig = field(default_factory=IgnoreConfig)
    lint: bool = True
    verbose: bool = False
    diff: bool | str = True
    failOn: str = "error"
    customRulesOnly: bool = False
    share: bool | None = True
    offline: bool | None = True
    rootDir: str | None = None
    respectInlineDisables: bool = True
    adoptExistingLintConfig: bool = True


def load_from_pyproject(pyproject_path: Path) -> dict | None:
    """Extract [tool.fastapi-doctor] section from pyproject.toml."""
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        return data.get("tool", {}).get("fastapi-doctor")
    except (tomllib.TOMLDecodeError, OSError):
        return None


def load_from_config_json(config_path: Path) -> dict | None:
    """Load fastapi-doctor.config.json."""
    try:
        with open(config_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def find_config_files(start_dir: Path) -> list[Path]:
    """Walk up from start_dir looking for config files. Stop at .git/."""
    configs = []
    current = start_dir.resolve()

    while True:
        toml_path = current / "pyproject.toml"
        json_path = current / "fastapi-doctor.config.json"

        if toml_path.exists():
            configs.append(toml_path)

        if json_path.exists():
            configs.append(json_path)

        if (current / ".git").exists():
            break

        parent = current.parent
        if parent == current:
            break
        current = parent

    return configs


def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge two dicts. override values win."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def load_config(start_dir: Path) -> FastapiDoctorConfig:
    """Load and merge all config files from start_dir up to project root."""
    config_paths = reversed(find_config_files(start_dir))

    merged: dict = {}
    for path in config_paths:
        if path.suffix == ".toml":
            data = load_from_pyproject(path)
        else:
            data = load_from_config_json(path)

        if data:
            merged = deep_merge(merged, data)

    # Convert nested dicts from TOML/JSON to dataclass instances
    ignore_data = merged.pop("ignore", {})
    if isinstance(ignore_data, dict):
        overrides_raw = ignore_data.pop("overrides", [])
        overrides = [OverrideConfig(**o) for o in overrides_raw]
        ignore_data["overrides"] = overrides
        merged["ignore"] = IgnoreConfig(**ignore_data)

    return FastapiDoctorConfig(**merged)


def should_skip_file(
    file_path: Path, scan_root: Path, config: FastapiDoctorConfig
) -> bool:
    """Check if a file should be skipped based on ignore.files glob patterns."""
    try:
        rel = file_path.resolve().relative_to(scan_root.resolve())
    except ValueError:
        return False

    rel_str = str(rel).replace("\\", "/")
    for pattern in config.ignore.files:
        if Path(rel_str).match(pattern):
            return True
    return False


def is_rule_suppressed(
    rule_id: str, file_path: str | Path, scan_root: Path, config: FastapiDoctorConfig
) -> bool:
    """Check if a rule is suppressed globally or via per-file override."""
    if rule_id in config.ignore.rules:
        return True

    if not config.ignore.overrides:
        return False

    file_path = Path(file_path)
    try:
        rel = file_path.resolve().relative_to(scan_root.resolve())
    except ValueError:
        return False

    rel_str = str(rel).replace("\\", "/")

    for override in config.ignore.overrides:
        if any(Path(rel_str).match(p) for p in override.files):
            if override.rules is None:
                return True
            if rule_id in override.rules:
                return True

    return False
