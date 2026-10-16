"""The initial, explicitly approved database model."""

from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Record:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class User(Record, Base):
    __tablename__ = "users"
    username: Mapped[str] = mapped_column(String(80), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    display_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default="admin")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class AuthSession(Record, Base):
    __tablename__ = "auth_sessions"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    access_hash: Mapped[str] = mapped_column(String(64), unique=True)
    refresh_hash: Mapped[str] = mapped_column(String(64), unique=True)
    access_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    refresh_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Company(Record, Base):
    __tablename__ = "companies"
    name: Mapped[str] = mapped_column(String(200), index=True)
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    industry: Mapped[str] = mapped_column(String(100), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)


class CompanyFact(Record, Base):
    __tablename__ = "company_facts"
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(300))
    source_url: Mapped[str] = mapped_column(Text, default="")
    fact_date: Mapped[date | None] = mapped_column(Date)


class Candidate(Record, Base):
    __tablename__ = "candidates"
    name: Mapped[str] = mapped_column(String(100), index=True)
    contacted_on: Mapped[date | None] = mapped_column(Date)
    current_company_id: Mapped[str | None] = mapped_column(ForeignKey("companies.id"))
    current_company_name: Mapped[str] = mapped_column(String(200), default="")
    current_title: Mapped[str] = mapped_column(String(200), default="")
    contact_methods: Mapped[list] = mapped_column(JSON, default=list)
    resume_source: Mapped[str] = mapped_column(String(200), default="")
    custom_fields: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)


class Employment(Record, Base):
    __tablename__ = "employments"
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"), index=True)
    company_id: Mapped[str | None] = mapped_column(ForeignKey("companies.id"))
    company_name: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(200))
    start_month: Mapped[str | None] = mapped_column(String(7))
    end_month: Mapped[str | None] = mapped_column(String(7))
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(Text, default="")


class Job(Record, Base):
    __tablename__ = "jobs"
    __table_args__ = (CheckConstraint("team_size IS NULL OR team_size >= 0", name="ck_job_team_size"),)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    team_size: Mapped[int | None] = mapped_column(Integer)
    reports_to: Mapped[str] = mapped_column(String(200), default="")
    business_context: Mapped[str] = mapped_column(Text, default="")
    jd_text: Mapped[str] = mapped_column(Text, default="")
    requirements: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default="open")
    custom_fields: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)


class Application(Record, Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job"),)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"), index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")


class Communication(Record, Base):
    __tablename__ = "communications"
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"), index=True)
    application_id: Mapped[str | None] = mapped_column(ForeignKey("applications.id"))
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    channel: Mapped[str] = mapped_column(String(50), default="其他")
    content: Mapped[str] = mapped_column(Text)
    outcome: Mapped[str] = mapped_column(Text, default="")
    next_step: Mapped[str] = mapped_column(Text, default="")
    follow_up_on: Mapped[date | None] = mapped_column(Date)


class FileAsset(Record, Base):
    __tablename__ = "file_assets"
    owner_type: Mapped[str] = mapped_column(String(20))
    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    original_name: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(100))
    size: Mapped[int] = mapped_column(Integer)
    checksum: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(36), unique=True)
    parse_status: Mapped[str] = mapped_column(String(30), default="not_started")
