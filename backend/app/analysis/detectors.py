import hashlib
import re
from collections import defaultdict

from app.analysis.contracts import FindingSeverity, RawFinding, SourceFile

SOURCE_EXTENSIONS = {
    ".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript", ".js": "JavaScript",
    ".jsx": "JavaScript", ".java": "Java", ".go": "Go", ".rb": "Ruby", ".php": "PHP",
    ".cs": "C#", ".rs": "Rust", ".sql": "SQL", ".yml": "YAML", ".yaml": "YAML",
}


def language_for(path: str) -> str | None:
    suffix = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return SOURCE_EXTENSIONS.get(suffix)


def snippet_at(content: str, line: int) -> str:
    lines = content.splitlines()
    return lines[line - 1].strip()[:500] if 0 < line <= len(lines) else ""


def finding(file: SourceFile, line: int, rule: str, category: str, severity: FindingSeverity, confidence: int, title: str, explanation: str, fix: str) -> RawFinding:
    return RawFinding(rule, category, severity, confidence, file.path, line, title, explanation, fix, snippet_at(file.content, line))


SECRET_RE = re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*[\"'][A-Za-z0-9_\-]{12,}[\"']")
SQL_RE = re.compile(r"(?i)(execute|query)\s*\(\s*(f[\"']|[\"'].*(?:SELECT|INSERT|UPDATE|DELETE).*\+)")
INSECURE_RE = re.compile(r"\b(eval|exec|pickle\.loads|yaml\.load\s*\()")
TODO_RE = re.compile(r"\b(TODO|FIXME|HACK)\b")
BAD_NAME_RE = re.compile(r"\b(?:var|data|temp|foo|bar|x1)\b")


def security_findings(file: SourceFile) -> list[RawFinding]:
    findings: list[RawFinding] = []
    for number, text in enumerate(file.content.splitlines(), start=1):
        if SECRET_RE.search(text):
            findings.append(finding(file, number, "CG-SEC-001", "security", FindingSeverity.CRITICAL, 95, "Hardcoded credential", "A value that looks like a secret is committed to source. It can be exposed through repository history, logs, and builds.", "Move the value to a secret manager or environment variable, rotate it, and remove it from Git history."))
        if SQL_RE.search(text):
            findings.append(finding(file, number, "CG-SEC-002", "security", FindingSeverity.HIGH, 88, "Potential SQL injection", "SQL is assembled from program text rather than parameterized inputs, allowing untrusted values to change a query.", "Use the database driver's parameter binding API and keep SQL structure separate from user values."))
        if INSECURE_RE.search(text):
            findings.append(finding(file, number, "CG-SEC-003", "security", FindingSeverity.HIGH, 82, "Dangerous dynamic execution", "Dynamic code deserialization or execution can run attacker-controlled instructions when inputs are not strictly trusted.", "Replace dynamic execution with a typed parser or allow-list; use safe_load for YAML."))
        if "verify=False" in text or "rejectUnauthorized: false" in text:
            findings.append(finding(file, number, "CG-SEC-004", "security", FindingSeverity.HIGH, 97, "TLS verification disabled", "Certificate validation is disabled, making connections vulnerable to interception.", "Enable certificate verification and configure an appropriate CA bundle if needed."))
    return findings


def quality_findings(file: SourceFile) -> list[RawFinding]:
    findings: list[RawFinding] = []
    branching = 0
    for number, text in enumerate(file.content.splitlines(), start=1):
        if re.search(r"\b(if|elif|else if|for|while|case|catch)\b", text):
            branching += 1
        if TODO_RE.search(text):
            findings.append(finding(file, number, "CG-QLT-001", "quality", FindingSeverity.LOW, 92, "Deferred maintenance marker", "A TODO/FIXME/HACK marker indicates acknowledged work that should be tracked and time-bounded.", "Create or link a tracked work item, then replace the marker with a concise reference."))
        if BAD_NAME_RE.search(text) and not text.lstrip().startswith(("#", "//")):
            findings.append(finding(file, number, "CG-QLT-002", "quality", FindingSeverity.LOW, 68, "Unclear identifier", "A generic identifier hides the role and lifetime of this value, increasing review and maintenance effort.", "Rename it for the business concept or data shape it represents."))
    if branching > 15:
        findings.append(finding(file, 1, "CG-QLT-003", "quality", FindingSeverity.MEDIUM, 80, "High cyclomatic complexity", f"This file has {branching} branch points, which makes behavioral paths difficult to test and reason about.", "Extract cohesive decisions into named functions and add focused tests for each branch."))
    return findings


def architecture_findings(files: list[SourceFile]) -> list[RawFinding]:
    findings: list[RawFinding] = []
    for file in files:
        normalized = file.path.lower()
        if "/domain/" in normalized and re.search(r"(flask|fastapi|requests|sqlalchemy|django)", file.content, re.I):
            findings.append(finding(file, 1, "CG-ARC-001", "architecture", FindingSeverity.MEDIUM, 75, "Domain layer depends on infrastructure", "Domain code imports delivery or persistence concerns, reducing portability and making business rules harder to test.", "Define a port/interface in the domain layer and inject the infrastructure implementation from the application layer."))
    return findings


def duplicate_findings(files: list[SourceFile]) -> list[RawFinding]:
    blocks: dict[str, list[tuple[SourceFile, int]]] = defaultdict(list)
    for file in files:
        lines = [line.strip() for line in file.content.splitlines() if line.strip() and not line.strip().startswith(("#", "//"))]
        for index in range(0, max(0, len(lines) - 5)):
            block = "\n".join(lines[index:index + 6])
            if len(block) > 100:
                blocks[hashlib.sha256(block.encode()).hexdigest()].append((file, index + 1))
    results: list[RawFinding] = []
    for occurrences in blocks.values():
        if len(occurrences) > 1:
            file, line = occurrences[0]
            results.append(finding(file, line, "CG-QLT-004", "quality", FindingSeverity.MEDIUM, 78, "Duplicated code block", f"A six-line code block appears {len(occurrences)} times. Duplicates diverge and make changes more expensive.", "Extract the shared behavior into a well-named function or shared module."))
    return results


def dependency_findings(files: list[SourceFile]) -> list[RawFinding]:
    results: list[RawFinding] = []
    vulnerable = {"lodash@4.17.15", "django@2.2.0", "requests@2.19.0", "log4j-core:2.14.1"}
    for file in files:
        if file.path.endswith(("package.json", "requirements.txt", "pom.xml")):
            for number, text in enumerate(file.content.splitlines(), start=1):
                if any(package in text.replace('"', '').replace(' ', '') for package in vulnerable):
                    results.append(finding(file, number, "CG-DEP-001", "dependency", FindingSeverity.HIGH, 90, "Known vulnerable dependency version", "This dependency version is in the built-in advisory demonstration set. A production provider should query OSV/GitHub Advisory data continuously.", "Upgrade to a patched version after checking its release notes and running the dependency test suite."))
    return results

