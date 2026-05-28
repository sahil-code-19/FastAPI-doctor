from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class Diagnostic:
    file_path: str
    rule: str
    severity: Severity
    message: str
    line: int
    column: int
    help: str = ""


@dataclass
class RuleDefinition:
    id: str
    severity: Severity
    description: str
    recommendation: str


@dataclass
class ScanResult:
    diagnostics: list[Diagnostic]
    files_scanned: int
    elapsed_ms: float


@dataclass
class ScoreResult:
    score: int
    label: str
