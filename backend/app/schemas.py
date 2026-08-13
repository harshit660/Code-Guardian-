from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import AnalysisStatus, Severity


class Message(BaseModel):
    detail: str


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RepositoryCreate(BaseModel):
    github_owner: str = Field(pattern=r"^[A-Za-z0-9_.-]+$")
    github_name: str = Field(pattern=r"^[A-Za-z0-9_.-]+$")
    default_branch: str = Field(default="main", max_length=255)


class RepositoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    github_owner: str
    github_name: str
    default_branch: str
    created_at: datetime


class AnalysisCreate(BaseModel):
    branch: str = Field(default="main", max_length=255)


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    rule_id: str
    category: str
    severity: Severity
    confidence: int
    file_path: str
    start_line: int
    end_line: int
    title: str
    explanation: str
    suggested_fix: str
    code_snippet: str | None
    reviewed: bool


class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    repository_id: UUID
    branch: str
    commit_sha: str | None
    status: AnalysisStatus
    quality_score: int | None
    security_score: int | None
    maintainability_score: int | None
    architecture_score: int | None
    technical_debt_minutes: int | None
    language_breakdown: dict
    error: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class AnalysisDetail(AnalysisOut):
    findings: list[FindingOut]


class PullRequestReviewRequest(BaseModel):
    pull_number: int = Field(gt=0)
    finding_ids: list[UUID] = Field(min_length=1, max_length=50)


class PullRequestReviewResult(BaseModel):
    submitted: int
    skipped: int

