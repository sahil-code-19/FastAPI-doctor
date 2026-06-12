import textwrap
from pathlib import Path

from fastapi_doctor.file_ignore import (
    build_file_ignore_spec,
    should_skip_file,
    _load_gitignore_patterns,
    _load_ruff_exclude_patterns,
    _load_gitattributes_vendored_patterns,
)


def _write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n")


def test_gitignore_skips_files(tmp_path):
    _write_file(
        tmp_path / ".gitignore",
        """
        __pycache__/
        *.pyc
        secrets.py
    """,
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("")
    (tmp_path / "src" / "secrets.py").write_text("")
    (tmp_path / "src" / "__pycache__").mkdir()
    (tmp_path / "src" / "__pycache__" / "cached.py").write_text("")

    spec = build_file_ignore_spec(tmp_path)

    assert not should_skip_file(tmp_path / "src" / "app.py", tmp_path, spec)
    assert should_skip_file(tmp_path / "src" / "secrets.py", tmp_path, spec)
    assert should_skip_file(
        tmp_path / "src" / "__pycache__" / "cached.py", tmp_path, spec
    )


def test_ruff_exclude_skips_files(tmp_path):
    _write_file(
        tmp_path / ".ruff.toml",
        'exclude = ["migrations/*", "scripts/**"]\n',
    )
    (tmp_path / "migrations").mkdir()
    (tmp_path / "migrations" / "001.py").write_text("")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("")

    spec = build_file_ignore_spec(tmp_path)

    assert should_skip_file(tmp_path / "migrations" / "001.py", tmp_path, spec)
    assert not should_skip_file(tmp_path / "src" / "app.py", tmp_path, spec)


def test_ruff_toplevel_exclude_skips_files(tmp_path):
    _write_file(
        tmp_path / "ruff.toml",
        """
        exclude = ["generated/*"]
    """,
    )
    (tmp_path / "generated").mkdir()
    (tmp_path / "generated" / "auto.py").write_text("")
    (tmp_path / "src" / "app.py").parent.mkdir(parents=True)
    (tmp_path / "src" / "app.py").write_text("")

    spec = build_file_ignore_spec(tmp_path)

    assert should_skip_file(tmp_path / "generated" / "auto.py", tmp_path, spec)
    assert not should_skip_file(tmp_path / "src" / "app.py", tmp_path, spec)


def test_gitattributes_vendored_skips_files(tmp_path):
    _write_file(
        tmp_path / ".gitattributes",
        """
        vendor/** linguist-vendored
        generated.py linguist-generated
    """,
    )
    (tmp_path / "vendor").mkdir()
    (tmp_path / "vendor" / "lib.py").write_text("")
    (tmp_path / "generated.py").write_text("")
    (tmp_path / "src" / "app.py").parent.mkdir(parents=True)
    (tmp_path / "src" / "app.py").write_text("")

    spec = build_file_ignore_spec(tmp_path)

    assert should_skip_file(tmp_path / "vendor" / "lib.py", tmp_path, spec)
    assert should_skip_file(tmp_path / "generated.py", tmp_path, spec)
    assert not should_skip_file(tmp_path / "src" / "app.py", tmp_path, spec)


def test_combined_ignores_merge(tmp_path):
    _write_file(tmp_path / ".gitignore", "secrets.py")
    _write_file(
        tmp_path / ".ruff.toml",
        'exclude = ["migrations/*"]\n',
    )
    (tmp_path / "secrets.py").write_text("")
    (tmp_path / "migrations" / "001.py").parent.mkdir(parents=True)
    (tmp_path / "migrations" / "001.py").write_text("")
    (tmp_path / "src" / "app.py").parent.mkdir(parents=True)
    (tmp_path / "src" / "app.py").write_text("")

    spec = build_file_ignore_spec(tmp_path)

    assert should_skip_file(tmp_path / "secrets.py", tmp_path, spec)
    assert should_skip_file(tmp_path / "migrations" / "001.py", tmp_path, spec)
    assert not should_skip_file(tmp_path / "src" / "app.py", tmp_path, spec)


def test_no_ignore_files_skips_nothing(tmp_path):
    (tmp_path / "src" / "app.py").parent.mkdir(parents=True)
    (tmp_path / "src" / "app.py").write_text("")

    spec = build_file_ignore_spec(tmp_path)

    assert not should_skip_file(tmp_path / "src" / "app.py", tmp_path, spec)


def test_should_skip_file_outside_root(tmp_path):
    (tmp_path / ".gitignore").write_text("*.py")
    outside = tmp_path / ".." / "other"
    spec = build_file_ignore_spec(tmp_path)
    assert not should_skip_file(outside, tmp_path, spec)


def test_pyproject_ruff_exclude_skips_files(tmp_path):
    _write_file(
        tmp_path / "pyproject.toml",
        """[tool.ruff]
exclude = ["migrations/*"]""",
    )
    (tmp_path / "migrations" / "001.py").parent.mkdir(parents=True)
    (tmp_path / "migrations" / "001.py").write_text("")
    (tmp_path / "src" / "app.py").parent.mkdir(parents=True)
    (tmp_path / "src" / "app.py").write_text("")

    spec = build_file_ignore_spec(tmp_path)

    assert should_skip_file(tmp_path / "migrations" / "001.py", tmp_path, spec)
    assert not should_skip_file(tmp_path / "src" / "app.py", tmp_path, spec)
