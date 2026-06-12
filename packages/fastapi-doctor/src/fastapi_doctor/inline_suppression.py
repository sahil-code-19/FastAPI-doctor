import re
from .models import Diagnostic

_DISABLE_LINE_RE = re.compile(r"#\s*fastapi-doctor-disable-line\s*(.*?)\s*$")
_DISABLE_NEXT_RE = re.compile(r"^\s*#\s*fastapi-doctor-disable-next-line\s*(.*)$")

_SUPPRESS_ALL = object()


def parse_inline_suppressions(source: str) -> dict[int, set[str] | object]:
    """Scan source for inline disable comments.

    Returns: {line_number: set(rule_ids) | _SUPPRESS_ALL}
    _SUPPRESS_ALL means "suppress every rule on this line".
    """
    lines = source.split("\n")
    suppressions: dict[int, set[str] | object] = {}

    disable_line_lines: set[int] = set()
    for i, line in enumerate(lines, start=1):
        m = _DISABLE_LINE_RE.search(line)
        if m:
            raw = m.group(1).strip()
            disable_line_lines.add(i)
            suppressions[i] = (
                _SUPPRESS_ALL
                if not raw
                else {r.strip() for r in raw.split(",") if r.strip()}
            )

    chained_rules: set[str] = set()
    chained_all = False
    is_first_in_chain = True

    for i, line in enumerate(lines, start=1):
        m = _DISABLE_NEXT_RE.match(line)
        if m:
            raw = m.group(1).strip()
            if raw:
                chained_rules.update(r.strip() for r in raw.split(","))
            else:
                chained_all = True

            target = _find_next_code_line(lines, i + 1)
            if target is not None:
                func_end = _find_function_end(lines, target)
                rules = _SUPPRESS_ALL if chained_all else set(chained_rules)

                for line_no in range(target, func_end + 1):
                    if line_no in disable_line_lines:
                        continue  # disable-line takes priority
                    existing = suppressions.get(line_no)
                    if existing is None or is_first_in_chain:
                        suppressions[line_no] = rules
                    elif existing is not _SUPPRESS_ALL:
                        existing |= rules

                is_first_in_chain = False
            continue

        if not _DISABLE_NEXT_RE.match(line):
            chained_rules.clear()
            chained_all = False
            is_first_in_chain = True

    return suppressions


def _find_next_code_line(lines: list[str], start: int) -> int | None:
    """Find the next non-blank code line. Skips decorators to the actual function."""
    i = start
    while i <= len(lines):
        stripped = lines[i - 1].strip()
        if stripped and not stripped.startswith("#"):
            if stripped.startswith("@"):
                i += 1
                while i <= len(lines):
                    inside = lines[i - 1].strip()
                    if inside.startswith(("def ", "async def ", "class ", "@")):
                        break
                    i += 1
                continue
            return i
        i += 1
    return None


def _find_function_end(lines: list[str], func_start: int) -> int:
    """Find where a function body ends — the next top-level declaration or end of file.

    A top-level declaration is a line starting with def, async def, class, or @
    at the SAME indentation level as the function definition.
    """
    func_line = lines[func_start - 1]

    indent = len(func_line) - len(func_line.lstrip())
    for i in range(func_start + 1, len(lines) + 1):
        line = lines[i - 1]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        line_indent = len(line) - len(line.lstrip())
        if line_indent <= indent and (
            stripped.startswith(("def ", "async def ", "class ", "@"))
        ):
            return i - 1
    return len(lines)


def is_diagnostic_suppressed(
    diag: Diagnostic, suppressions: dict[int, set[str] | object]
) -> bool:
    line_sup = suppressions.get(diag.line)
    if line_sup is None:
        return False
    if line_sup is _SUPPRESS_ALL:
        return True
    if diag.rule in line_sup:
        return True
    return any(diag.rule.endswith("/" + r) for r in line_sup)
