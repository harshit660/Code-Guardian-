import hashlib
from datetime import UTC, datetime
from uuid import UUID

import structlog
from celery import Task

from app.analysis.pipeline import AnalysisPipeline
from app.database import SessionLocal
from app.integrations.github import GitHubGateway
from app.models import Analysis, AnalysisStatus, Finding, Severity
from app.workers.celery_app import celery_app

log = structlog.get_logger(__name__)


def fingerprint(rule_id: str, path: str, line: int, snippet: str) -> str:
    return hashlib.sha256(f"{rule_id}:{path}:{line}:{snippet}".encode()).hexdigest()


@celery_app.task(bind=True, autoretry_for=(OSError,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def analyze_repository(self: Task, analysis_id: str) -> None:
    with SessionLocal() as db:
        analysis = db.get(Analysis, UUID(analysis_id))
        if not analysis:
            log.warning("analysis_not_found", analysis_id=analysis_id)
            return
        analysis.status = AnalysisStatus.running
        analysis.started_at = datetime.now(UTC)
        db.commit()
        try:
            repository = analysis.repository
            snapshot = GitHubGateway().snapshot(repository.github_owner, repository.github_name, analysis.branch)
            result = AnalysisPipeline().run(snapshot.files)
            analysis.commit_sha = snapshot.commit_sha
            analysis.quality_score = result.quality_score
            analysis.security_score = result.security_score
            analysis.maintainability_score = result.maintainability_score
            analysis.architecture_score = result.architecture_score
            analysis.technical_debt_minutes = result.technical_debt_minutes
            analysis.language_breakdown = result.language_breakdown
            for raw in result.findings:
                db.add(Finding(
                    analysis_id=analysis.id,
                    rule_id=raw.rule_id,
                    category=raw.category,
                    severity=Severity(raw.severity.value),
                    confidence=raw.confidence,
                    file_path=raw.file_path,
                    start_line=raw.line,
                    end_line=raw.line,
                    title=raw.title,
                    explanation=raw.explanation,
                    suggested_fix=raw.suggested_fix,
                    code_snippet=raw.snippet,
                    fingerprint=fingerprint(raw.rule_id, raw.file_path, raw.line, raw.snippet),
                ))
            analysis.status = AnalysisStatus.completed
            analysis.completed_at = datetime.now(UTC)
            db.commit()
            log.info("analysis_completed", analysis_id=analysis_id, finding_count=len(result.findings))
        except Exception as exc:
            analysis.status = AnalysisStatus.failed
            analysis.error = str(exc)[:2000]
            analysis.completed_at = datetime.now(UTC)
            db.commit()
            log.exception("analysis_failed", analysis_id=analysis_id)
            raise

