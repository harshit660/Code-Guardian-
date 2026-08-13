from dataclasses import dataclass
from enum import StrEnum


class FindingSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass(frozen=True)
class SourceFile:
    path: str
    content: str


@dataclass(frozen=True)
class RawFinding:
    rule_id: str
    category: str
    severity: FindingSeverity
    confidence: int
    file_path: str
    line: int
    title: str
    explanation: str
    suggested_fix: str
    snippet: str


@dataclass(frozen=True)
class AnalysisResult:
    findings: list[RawFinding]
    language_breakdown: dict[str, int]
    quality_score: int
    security_score: int
    maintainability_score: int
    architecture_score: int
    technical_debt_minutes: int

