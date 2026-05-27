import argparse
import sys
from pathlib import Path
from .scanner import scan_directory
from .scoring import calculate_score
from .reporter import print_header, print_diagnostics, print_score, print_summary
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
    
    args = parser.parse_args()
    
    directory = Path(args.directory).resolve()
    if not directory.is_dir():
        print(f"Error: {directory} is not a directory", file=sys.stderr)
        sys.exit(1)
    
    if not args.score:
        print_header(VERSION)
    
    result = scan_directory(directory)
    score_result = calculate_score(result.diagnostics)
    
    if args.score:
        print(score_result.score)
        return
    
    print_diagnostics(result.diagnostics, verbose=args.verbose)
    print()
    print_score(score_result)
    print_summary(result.diagnostics, result.files_scanned, result.elapsed_ms)
    
    # Exit with error if there are errors
    if any(d.severity.value == "error" for d in result.diagnostics):
        sys.exit(1)
if __name__ == "__main__":
    main()