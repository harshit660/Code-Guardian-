from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import current_user
from app.integrations.github import GitHubGateway, GitHubGatewayError
from app.models import Repository, User
from app.schemas import RepositoryCreate, RepositoryOut

router = APIRouter()


def owned_repository(repository_id: UUID, user: User, db: Session) -> Repository:
    repository = db.scalar(select(Repository).where(Repository.id == repository_id, Repository.owner_id == user.id))
    if not repository:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return repository


@router.get("", response_model=list[RepositoryOut])
def list_repositories(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[Repository]:
    return list(db.scalars(select(Repository).where(Repository.owner_id == user.id).order_by(Repository.created_at.desc())))


@router.post("", response_model=RepositoryOut, status_code=status.HTTP_201_CREATED)
def connect_repository(payload: RepositoryCreate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Repository:
    existing = db.scalar(select(Repository).where(Repository.owner_id == user.id, Repository.github_owner == payload.github_owner, Repository.github_name == payload.github_name))
    if existing:
        return existing
    repository = Repository(owner_id=user.id, **payload.model_dump())
    db.add(repository)
    db.commit()
    db.refresh(repository)
    return repository


@router.get("/{repository_id}/branches", response_model=list[str])
def branches(repository_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[str]:
    repository = owned_repository(repository_id, user, db)
    try:
        return GitHubGateway().branches(repository.github_owner, repository.github_name)
    except GitHubGatewayError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
