from collections import Counter

from app.analysis.contracts import AnalysisResult, FindingSeverity, SourceFile
from app.analysis.detectors import architecture_findings, dependency_findings, duplicate_findings, language_for, quality_findings, security_findings
from app.analysis.llm import get_reasoner


WEIGHTS = {
    FindingSeverity.CRITICAL: 25,
    FindingSeverity.HIGH: 12,
    FindingSeverity.MEDIUM: 6,
    FindingSeverity.LOW: 2,
    FindingSeverity.INFO: 0,
}


def _score(findings, categories: set[str]) -> int:
    penalty = sum(WEIGHTS[f.severity] for f in findings if f.category in categories)
    return max(0, min(100, 100 - penalty))


class AnalysisPipeline:
    """Orchestrates ingestion output through language, static, dependency, and reasoning stages."""

    def run(self, files: list[SourceFile]) -> AnalysisResult:
        source_files = [item for item in files if language_for(item.path)]
        languages = Counter(language_for(item.path) for item in source_files)
        static = [finding for source in source_files for finding in security_findings(source) + quality_findings(source)]
        findings = static + dependency_findings(files) + duplicate_findings(source_files) + architecture_findings(source_files)
        reasoner = get_reasoner()
        enriched = [reasoner.enrich(item) for item in findings]
        security = _score(enriched, {"security", "dependency"})
        quality = _score(enriched, {"quality"})
        architecture = _score(enriched, {"architecture"})
        maintainability = max(0, round((quality + architecture) / 2))
        debt = sum({FindingSeverity.CRITICAL: 120, FindingSeverity.HIGH: 60, FindingSeverity.MEDIUM: 30, FindingSeverity.LOW: 10, FindingSeverity.INFO: 5}[f.severity] for f in enriched)
        return AnalysisResult(enriched, dict(languages), quality, security, maintainability, architecture, debt)

