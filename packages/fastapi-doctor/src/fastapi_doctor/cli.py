import argparse
import sys
from pathlib import Path

from .scanner import scan_directory, SKIP_DIRS
from .scoring import calculate_score
from .reporter import print_header, print_diagnostics, print_score, print_summary
from .json_reporter import format_json, format_json_compact, format_error_json
from .annotations import print_annotations
from .git_diff import (
    get_changed_files,
    get_staged_files,
    filter_python_files,
)

VERSION = "0.3.2"


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "install":
        sys.argv.pop(1)
        install_main()
        return

    scan_main()


def install_main():
    parser = argparse.ArgumentParser(
        prog="fastapi-therapist install",
        description="Install fastapi-therapist skill for AI agents",
    )
    parser.add_argument("-y", "--yes", action="store_true", help="Skip prompts")
    parser.add_argument("--dry-run", action="store_true", help="Preview installation")
    parser.add_argument("-c", "--cwd", type=Path, default=None, help="Project root")
    args = parser.parse_args()

    from .installer import run_install

    run_install(yes=args.yes, dry_run=args.dry_run, cwd=args.cwd)


def scan_main():
    parser = argparse.ArgumentParser(
        prog="fastapi-therapist",
        description="Diagnose FastAPI codebases for best practices",
    )
    parser.add_argument("directory", nargs="?", default=".", help="Directory to scan")
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {VERSION}"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show all file locations"
    )
    parser.add_argument("--score", action="store_true", help="Output only the score")
    parser.add_argument(
        "--diff",
        nargs="?",
        const="main",
        default=None,
        help="Only scan files changed vs base branch (default: main)",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Only scan staged files (for pre-commit hooks)",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Ignore inline suppression comments — reveal all hidden issues",
    )
    parser.add_argument(
        "--annotations",
        action="store_true",
        help="Output GitHub Actions workflow commands for inline PR annotations",
    )
    parser.add_argument(
        "--ruff",
        action="store_true",
        default=None,
        help="Include ruff linting results in the report",
    )
    parser.add_argument(
        "--no-ruff",
        action="store_false",
        dest="ruff",
        help="Skip ruff linting even if enabled in config",
    )
    parser.add_argument(
        "--vulture",
        action="store_true",
        default=None,
        help="Run vulture dead code detection (default: on)",
    )
    parser.add_argument(
        "--no-vulture",
        action="store_false",
        dest="vulture",
        help="Skip vulture dead code detection",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON (for CI/programmatic use)",
    )
    parser.add_argument(
        "--json-compact",
        action="store_true",
        help="Output results as compact (single-line) JSON",
    )
    parser.add_argument(
        "--fail-on",
        choices=["error", "warning", "none"],
        default="error",
        help="Exit with non-zero if any diagnostic meets this severity (default: error)",
    )

    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    if not directory.is_dir():
        error_msg = f"Error: {directory} is not a directory"
        if args.json or args.json_compact:
            print(format_error_json(error_msg, str(directory), "full", VERSION))
        else:
            print(error_msg, file=sys.stderr)
        sys.exit(1)

    # Determine scan mode
    if args.staged:
        mode = "staged"
    elif args.diff is not None:
        mode = "diff"
    else:
        mode = "full"

    if args.staged:
        changed = get_staged_files(directory)
        files = filter_python_files(changed, SKIP_DIRS)
        if not files:
            msg = "No staged Python files to scan."
            if args.json or args.json_compact:
                print(
                    format_json_compact({}, str(directory), mode, VERSION)
                    if args.json_compact
                    else format_json(
                        {"diagnostics": [], "files_scanned": 0, "elapsed_ms": 0},
                        str(directory),
                        mode,
                        VERSION,
                    )
                )
            else:
                print(msg, file=sys.stderr)
            sys.exit(0)
    elif args.diff is not None:
        base = args.diff if args.diff != "main" else "main"
        changed = get_changed_files(directory, base=base)
        files = filter_python_files(changed, SKIP_DIRS)
        if not files:
            msg = f"No changed Python files vs {base}."
            if args.json or args.json_compact:
                dummy_result = type(
                    "ScanResult",
                    (),
                    {
                        "diagnostics": [],
                        "files_scanned": 0,
                        "elapsed_ms": 0,
                        "mode": mode,
                    },
                )
                print(
                    format_json_compact(dummy_result, str(directory), mode, VERSION)
                    if args.json_compact
                    else format_json(dummy_result, str(directory), mode, VERSION)
                )
            else:
                print(msg, file=sys.stderr)
            sys.exit(0)
    else:
        files = None
        base_branch = None

    try:
        if not (args.json or args.json_compact or args.score):
            print_header(VERSION)

        result = scan_directory(
            directory,
            files=files,
            audit=args.audit,
            mode=mode,
            ruff_flag=args.ruff,
            vulture_flag=args.vulture,
        )
        score_result = calculate_score(result.diagnostics)

        if args.score:
            print(score_result.score)
            return

        if args.json:
            print(
                format_json(
                    result,
                    str(directory),
                    mode,
                    VERSION,
                    base_branch=args.diff if mode == "diff" else None,
                )
            )
        elif args.json_compact:
            print(format_json_compact(result, str(directory), mode, VERSION))
        elif args.annotations:
            print_annotations(result.diagnostics, directory)
        else:
            print_diagnostics(result.diagnostics, verbose=args.verbose)
            print()
            print_score(score_result)
            print_summary(result.diagnostics, result.files_scanned, result.elapsed_ms)

        # Exit code based on fail-on
        if args.fail_on == "error" and any(
            d.severity.value == "error" for d in result.diagnostics
        ):
            sys.exit(1)
        elif args.fail_on == "warning" and any(
            d.severity.value in ("error", "warning") for d in result.diagnostics
        ):
            sys.exit(1)

    except Exception as exc:
        error_msg = f"{type(exc).__name__}: {exc}"
        if args.json or args.json_compact:
            print(
                format_error_json(
                    error_msg,
                    str(directory),
                    mode,
                    VERSION,
                    exception_type=type(exc).__name__,
                )
            )
        else:
            print(f"Error during scan: {error_msg}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
