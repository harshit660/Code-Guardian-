import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Severity(str, enum.Enum):
    critical = "CRITICAL"
    high = "HIGH"
    medium = "MEDIUM"
    low = "LOW"
    info = "INFO"


class AnalysisStatus(str, enum.Enum):
    queued = "QUEUED"
    running = "RUNNING"
    completed = "COMPLETED"
    failed = "FAILED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    repositories: Mapped[list["Repository"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    github_owner: Mapped[str] = mapped_column(String(100))
    github_name: Mapped[str] = mapped_column(String(100))
    default_branch: Mapped[str] = mapped_column(String(255), default="main")
    provider_installation_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    owner: Mapped[User] = relationship(back_populates="repositories")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="repository", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("repositories.id"), index=True)
    branch: Mapped[str] = mapped_column(String(255))
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[AnalysisStatus] = mapped_column(Enum(AnalysisStatus), default=AnalysisStatus.queued, index=True)
    quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    security_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    maintainability_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    architecture_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    technical_debt_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    repository: Mapped[Repository] = relationship(back_populates="analyses")
    findings: Mapped[list["Finding"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("analyses.id"), index=True)
    rule_id: Mapped[str] = mapped_column(String(120), index=True)
    category: Mapped[str] = mapped_column(String(80))
    severity: Mapped[Severity] = mapped_column(Enum(Severity), index=True)
    confidence: Mapped[int] = mapped_column(Integer)
    file_path: Mapped[str] = mapped_column(String(1000))
    start_line: Mapped[int] = mapped_column(Integer)
    end_line: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(500))
    explanation: Mapped[str] = mapped_column(Text)
    suggested_fix: Mapped[str] = mapped_column(Text)
    code_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    analysis: Mapped[Analysis] = relationship(back_populates="findings")

