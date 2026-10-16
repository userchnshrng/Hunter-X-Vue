from typing import Literal

from pydantic import Field

from app.schemas import Input


class PreviewInput(Input):
    revision: int = Field(ge=0)
    sheet_name: str = Field(min_length=1, max_length=100)
    header_row: int = Field(ge=1, le=20)
    mapping: dict[str, str] = Field(max_length=100)


class RowInput(Input):
    revision: int = Field(ge=1)
    corrections: dict[str, str] | None = None
    decision: Literal["", "create", "skip"] | None = None
    acknowledged: bool | None = None


class CommitInput(Input):
    revision: int = Field(ge=1)
    idempotency_key: str = Field(min_length=16, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
