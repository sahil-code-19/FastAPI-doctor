import subprocess
from pathlib import Path


def get_git_root(directory: Path) -> Path | None:
    """Find the nearest .git directory root."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=directory,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def get_changed_files(directory: Path, base: str = "main") -> set[Path]:
    """Get files changed vs base branch using git diff --name-only.

    Tries base, then 'master', then HEAD~1 as fallback.
    """
    git_root = get_git_root(directory)
    if git_root is None:
        return set()

    files = _diff_against_base(git_root, base)
    if files is not None:
        return files

    if base != "master":
        files = _diff_against_base(git_root, "master")
        if files is not None:
            return files

    return _diff_files(git_root, ["HEAD"]) or set()


def get_staged_files(directory: Path) -> set[Path]:
    """Get files staged in git using git diff --cached --name-only."""
    git_root = get_git_root(directory)
    if git_root is None:
        return set()
    return _diff_files(git_root, ["--cached"]) or set()


def _diff_against_base(git_root: Path, base: str) -> set[Path] | None:
    """Find common ancestor with base, diff only branch-unique changes."""
    check = subprocess.run(
        ["git", "rev-parse", "--verify", base],
        capture_output=True,
        text=True,
        cwd=git_root,
    )
    if check.returncode != 0:
        check = subprocess.run(
            ["git", "rev-parse", "--verify", f"origin/{base}"],
            capture_output=True,
            text=True,
            cwd=git_root,
        )
        if check.returncode != 0:
            return None
        base = f"origin/{base}"

    # Find common ancestor between base and HEAD
    merge_base = subprocess.run(
        ["git", "merge-base", base, "HEAD"],
        capture_output=True,
        text=True,
        cwd=git_root,
    )
    if merge_base.returncode != 0:
        return None

    # Diff from merge-base to HEAD — only changes on this branch
    return _diff_files(git_root, [merge_base.stdout.strip()])


def _diff_files(git_root: Path, extra_args: list[str]) -> set[Path] | None:
    """Run git diff --name-only with extra args."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", *extra_args],
            capture_output=True,
            text=True,
            cwd=git_root,
        )
        if result.returncode != 0:
            return None

        files: set[Path] = set()
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if line and line.endswith(".py"):
                full_path = (git_root / line).resolve()
                if full_path.exists():
                    files.add(full_path)
        return files
    except subprocess.SubprocessError:
        return None


def filter_python_files(files: set[Path], skip_dir: list[str]) -> list[Path]:
    """Filter to only Python files, excluding skip dirs."""
    result = []
    for f in files:
        if f.suffix != ".py":
            continue
        if any(part in skip_dir for part in f.parts):
            continue
        result.append(f)
    return sorted(result)
