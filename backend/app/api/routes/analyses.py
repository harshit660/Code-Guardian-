from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.routes.repositories import owned_repository
from app.database import get_db
from app.dependencies import current_user
from app.integrations.github import GitHubGateway, GitHubGatewayError
from app.models import Analysis, Finding, Repository, User
from app.schemas import AnalysisCreate, AnalysisDetail, AnalysisOut, PullRequestReviewRequest, PullRequestReviewResult
from app.workers.tasks import analyze_repository

router = APIRouter()


def owned_analysis(analysis_id: UUID, user: User, db: Session, eager: bool = False) -> Analysis:
    query = select(Analysis).join(Repository).where(Analysis.id == analysis_id, Repository.owner_id == user.id)
    if eager:
        query = query.options(selectinload(Analysis.findings))
    analysis = db.scalar(query)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return analysis


@router.post("/repositories/{repository_id}", response_model=AnalysisOut, status_code=status.HTTP_202_ACCEPTED)
def trigger_analysis(repository_id: UUID, payload: AnalysisCreate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Analysis:
    repository = owned_repository(repository_id, user, db)
    analysis = Analysis(repository_id=repository.id, branch=payload.branch)
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    try:
        analyze_repository.delay(str(analysis.id))
    except Exception as exc:
        # Preserve the queued record for operational retry rather than losing user intent.
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Analysis queue is unavailable; retry shortly") from exc
    return analysis


@router.get("/repositories/{repository_id}", response_model=list[AnalysisOut])
def list_analyses(repository_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[Analysis]:
    repository = owned_repository(repository_id, user, db)
    return list(db.scalars(select(Analysis).where(Analysis.repository_id == repository.id).order_by(Analysis.created_at.desc()).limit(30)))


@router.get("/{analysis_id}", response_model=AnalysisDetail)
def get_analysis(analysis_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Analysis:
    return owned_analysis(analysis_id, user, db, eager=True)


@router.post("/{analysis_id}/pull-request-review", response_model=PullRequestReviewResult)
def publish_pull_request_review(analysis_id: UUID, payload: PullRequestReviewRequest, user: User = Depends(current_user), db: Session = Depends(get_db)) -> PullRequestReviewResult:
    analysis = owned_analysis(analysis_id, user, db, eager=True)
    requested = set(payload.finding_ids)
    selected = [item for item in analysis.findings if item.id in requested]
    if not selected:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No requested findings belong to this analysis")
    comments = [
        {
            "path": item.file_path,
            "line": item.end_line,
            "side": "RIGHT",
            "body": f"**{item.severity.value}: {item.title}**\n\n{item.explanation}\n\n**Suggested fix:** {item.suggested_fix}",
        }
        for item in selected
    ]
    try:
        GitHubGateway().submit_review(analysis.repository.github_owner, analysis.repository.github_name, payload.pull_number, comments)
    except GitHubGatewayError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return PullRequestReviewResult(submitted=len(comments), skipped=len(payload.finding_ids) - len(comments))

