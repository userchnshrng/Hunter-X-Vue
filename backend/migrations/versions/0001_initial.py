"""Approved initial schema; no destructive downgrade is supplied."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def common():
    return [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def string(name, length=200, nullable=False, **kwargs):
    return sa.Column(name, sa.String(length), nullable=nullable, **kwargs)


def text(name, nullable=False):
    return sa.Column(name, sa.Text(), nullable=nullable)


def foreign(name, target, nullable=False):
    return sa.Column(name, sa.String(36), sa.ForeignKey(target), nullable=nullable)


def upgrade():
    op.create_table(
        "users",
        *common(),
        string("username", 80, unique=True),
        text("password_hash"),
        string("display_name", 100),
        string("role", 20),
        sa.Column("active", sa.Boolean, nullable=False),
    )
    op.create_table(
        "auth_sessions",
        *common(),
        foreign("user_id", "users.id"),
        string("access_hash", 64, unique=True),
        string("refresh_hash", 64, unique=True),
        sa.Column("access_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("refresh_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "companies",
        *common(),
        string("name"),
        sa.Column("aliases", sa.JSON, nullable=False),
        string("industry", 100),
        text("description"),
        sa.Column("version", sa.Integer, nullable=False),
    )
    op.create_table(
        "company_facts",
        *common(),
        foreign("company_id", "companies.id"),
        text("content"),
        string("source", 300),
        text("source_url"),
        sa.Column("fact_date", sa.Date),
    )
    op.create_table(
        "candidates",
        *common(),
        string("name", 100),
        sa.Column("contacted_on", sa.Date),
        foreign("current_company_id", "companies.id", nullable=True),
        string("current_company_name"),
        string("current_title"),
        sa.Column("contact_methods", sa.JSON, nullable=False),
        string("resume_source"),
        sa.Column("custom_fields", sa.JSON, nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
    )
    op.create_table(
        "employments",
        *common(),
        foreign("candidate_id", "candidates.id"),
        foreign("company_id", "companies.id", nullable=True),
        string("company_name"),
        string("title"),
        string("start_month", 7, nullable=True),
        string("end_month", 7, nullable=True),
        sa.Column("is_current", sa.Boolean, nullable=False),
        text("description"),
    )
    op.create_table(
        "jobs",
        *common(),
        foreign("company_id", "companies.id"),
        string("title"),
        sa.Column("team_size", sa.Integer),
        string("reports_to"),
        text("business_context"),
        text("jd_text"),
        sa.Column("requirements", sa.JSON, nullable=False),
        string("status", 30),
        sa.Column("custom_fields", sa.JSON, nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.CheckConstraint("team_size IS NULL OR team_size >= 0", name="ck_job_team_size"),
    )
    op.create_table(
        "applications",
        *common(),
        foreign("candidate_id", "candidates.id"),
        foreign("job_id", "jobs.id"),
        string("status", 30),
        sa.UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job"),
    )
    op.create_table(
        "communications",
        *common(),
        foreign("candidate_id", "candidates.id"),
        foreign("application_id", "applications.id", nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True)),
        string("channel", 50),
        text("content"),
        text("outcome"),
        text("next_step"),
        sa.Column("follow_up_on", sa.Date),
    )
    op.create_table(
        "file_assets",
        *common(),
        string("owner_type", 20),
        string("owner_id", 36),
        string("original_name", 255),
        string("media_type", 100),
        sa.Column("size", sa.Integer, nullable=False),
        string("checksum", 64),
        string("storage_key", 36, unique=True),
        string("parse_status", 30),
    )
    for table, columns in {
        "auth_sessions": ["user_id"],
        "companies": ["name"],
        "company_facts": ["company_id"],
        "candidates": ["name"],
        "employments": ["candidate_id"],
        "jobs": ["company_id", "title"],
        "applications": ["candidate_id", "job_id"],
        "communications": ["candidate_id"],
        "file_assets": ["owner_id"],
    }.items():
        for column in columns:
            op.create_index(f"ix_{table}_{column}", table, [column])


def downgrade():
    raise RuntimeError("Destructive downgrade requires a separate, explicitly approved migration plan.")
