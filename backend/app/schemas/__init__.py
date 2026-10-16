import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

JobStatus = Literal["draft", "open", "paused", "closed"]
ApplicationStatus = Literal[
    "pending", "to_contact", "contacting", "submitted", "interview", "offer", "hired", "hold"
]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(Input):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=1024)


class CompanyInput(Input):
    name: str = Field(min_length=1, max_length=200)
    aliases: list[str] = Field(default_factory=list, max_length=30)
    industry: str = Field(default="", max_length=100)
    description: str = Field(default="", max_length=20000)


class FactInput(Input):
    content: str = Field(min_length=1, max_length=20000)
    source: str = Field(min_length=1, max_length=300)
    source_url: str = Field(default="", max_length=2000)
    fact_date: date | None = None

    @field_validator("source_url")
    @classmethod
    def safe_url(cls, value):
        if value and not value.startswith(("https://", "http://")):
            raise ValueError("资料链接仅支持 http 或 https")
        return value


class Contact(Input):
    type: Literal["phone", "wechat", "email", "other"]
    value: str = Field(min_length=1, max_length=200)


class CandidateInput(Input):
    name: str = Field(min_length=1, max_length=100)
    contacted_on: date | None = None
    current_company_id: str | None = None
    current_company_name: str = Field(default="", max_length=200)
    current_title: str = Field(default="", max_length=200)
    contact_methods: list[Contact] = Field(default_factory=list, max_length=20)
    resume_source: str = Field(default="", max_length=200)
    custom_fields: dict = Field(default_factory=dict, max_length=50)


class EmploymentInput(Input):
    company_id: str | None = None
    company_name: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=200)
    start_month: str | None = None
    end_month: str | None = None
    is_current: bool = False
    description: str = Field(default="", max_length=20000)

    @field_validator("start_month", "end_month")
    @classmethod
    def month_format(cls, value):
        if value is not None and not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
            raise ValueError("年月应为 YYYY-MM")
        return value

    @model_validator(mode="after")
    def valid_range(self):
        if self.start_month and self.end_month and self.start_month > self.end_month:
            raise ValueError("结束年月不能早于开始年月")
        if self.is_current and self.end_month:
            raise ValueError("在职经历不能有结束年月")
        return self


class JobInput(Input):
    company_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=200)
    team_size: int | None = Field(default=None, ge=0, le=1000000, strict=True)
    reports_to: str = Field(default="", max_length=200)
    business_context: str = Field(default="", max_length=20000)
    jd_text: str = Field(default="", max_length=100000)
    requirements: list[str] = Field(default_factory=list, max_length=100)
    status: JobStatus = "open"
    custom_fields: dict = Field(default_factory=dict, max_length=50)


class ApplicationInput(Input):
    candidate_id: str
    job_id: str


class StatusInput(Input):
    status: ApplicationStatus


class CommunicationInput(Input):
    application_id: str | None = None
    occurred_at: datetime | None = None
    channel: str = Field(default="其他", max_length=50)
    content: str = Field(min_length=1, max_length=20000)
    outcome: str = Field(default="", max_length=20000)
    next_step: str = Field(default="", max_length=20000)
    follow_up_on: date | None = None

    @field_validator("occurred_at")
    @classmethod
    def timezone_required(cls, value):
        if value and value.tzinfo is None:
            raise ValueError("沟通时间必须包含时区")
        return value
