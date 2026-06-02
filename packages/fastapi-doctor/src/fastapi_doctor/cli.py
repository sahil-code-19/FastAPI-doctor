import argparse
import sys
from pathlib import Path

from .scanner import scan_directory
from .scoring import calculate_score
from .reporter import print_header, print_diagnostics, print_score, print_summary
from .scanner import SKIP_DIRS
from .git_diff import (
    get_changed_files,
    get_staged_files,
    get_git_root,
    filter_python_files,
)

VERSION = "0.1.0"
def main():
    parser = argparse.ArgumentParser(
        prog="fastapi-doctor",
        description="Diagnose FastAPI codebases for best practices",
    )
    parser.add_argument("directory", nargs="?", default=".", help="Directory to scan")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("--verbose", action="store_true", help="Show all file locations")
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

    args = parser.parse_args()
    
    directory = Path(args.directory).resolve()
    if not directory.is_dir():
        print(f"Error: {directory} is not a directory", file=sys.stderr)
        sys.exit(1)

    if args.staged:
        changed = get_staged_files(directory)
        files = filter_python_files(changed, SKIP_DIRS)
        if not files:
            print("No staged Python files to scan.", file=sys.stderr)
            sys.exit(0)
    elif args.diff is not None:
        base = args.diff if args.diff != "main" else "main"
        changed = get_changed_files(directory, base=base)
        files = filter_python_files(changed, SKIP_DIRS)
        if not files:
            print(f"No changed Python files vs {base}.", file=sys.stderr)
            sys.exit(0)
    else:
        files = None

    if not args.score:
        print_header(VERSION)

    result = scan_directory(directory, files=files)
    score_result = calculate_score(result.diagnostics)
    
    if args.score:
        print(score_result.score)
        return
    
    print_diagnostics(result.diagnostics, verbose=args.verbose)
    print()
    print_score(score_result)
    print_summary(result.diagnostics, result.files_scanned, result.elapsed_ms)

    if any(d.severity.value == "error" for d in result.diagnostics):
        sys.exit(1)
if __name__ == "__main__":
    main()
