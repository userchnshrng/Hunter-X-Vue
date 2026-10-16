"""Approved stage B: add definitions and import records; preserve all existing tables."""

import sqlalchemy as sa
from alembic import op

revision = "0002_stage_b"
down_revision = "0001"
branch_labels = None
depends_on = None


def common():
    return [
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade():
    op.create_table(
        "custom_field_definitions",
        *common(),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("key", sa.String(40), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("value_type", sa.String(20), nullable=False),
        sa.Column("options", sa.JSON, nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("required", sa.Boolean, nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.UniqueConstraint("entity_type", "key", name="uq_custom_field_key"),
        sa.CheckConstraint("entity_type IN ('candidate','job')", name="ck_field_entity"),
        sa.CheckConstraint("value_type IN ('text','number','date','select')", name="ck_field_type"),
    )
    op.create_table(
        "import_batches",
        *common(),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("file_format", sa.String(10), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("storage_key", sa.String(36), nullable=False, unique=True),
        sa.Column("size", sa.Integer, nullable=False),
        sa.Column("sheets", sa.JSON, nullable=False),
        sa.Column("sheet_name", sa.String(100), nullable=False),
        sa.Column("header_row", sa.Integer, nullable=False),
        sa.Column("mapping", sa.JSON, nullable=False),
        sa.Column("field_snapshot", sa.String(64), nullable=False),
        sa.Column("revision", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("counts", sa.JSON, nullable=False),
        sa.Column("idempotency_key", sa.String(100)),
        sa.Column("commit_digest", sa.String(64), nullable=False),
        sa.Column("committed_at", sa.DateTime(timezone=True)),
        sa.Column("result", sa.JSON, nullable=False),
        sa.UniqueConstraint("created_by", "idempotency_key", name="uq_import_idempotency"),
        sa.CheckConstraint(
            "status IN ('uploaded','review','ready','committed','cancelled')", name="ck_import_status"
        ),
    )
    op.create_index("ix_import_batches_created_by", "import_batches", ["created_by"])
    op.create_index("ix_import_batches_checksum", "import_batches", ["checksum"])
    op.create_table(
        "import_rows",
        *common(),
        sa.Column("batch_id", sa.String(36), sa.ForeignKey("import_batches.id"), nullable=False),
        sa.Column("sheet_name", sa.String(100), nullable=False),
        sa.Column("row_number", sa.Integer, nullable=False),
        *[
            sa.Column(name, kind, nullable=False)
            for name, kind in [
                ("original", sa.JSON),
                ("corrections", sa.JSON),
                ("normalized", sa.JSON),
                ("errors", sa.JSON),
                ("warnings", sa.JSON),
                ("duplicates", sa.JSON),
            ]
        ],
        sa.Column("decision", sa.String(10), nullable=False),
        sa.Column("acknowledged", sa.Boolean, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("candidate_id", sa.String(36), sa.ForeignKey("candidates.id")),
        sa.UniqueConstraint("batch_id", "sheet_name", "row_number", name="uq_import_row"),
    )
    op.create_index("ix_import_rows_batch_id", "import_rows", ["batch_id"])


def downgrade():
    raise RuntimeError("Destructive downgrade requires separate user authorization")
