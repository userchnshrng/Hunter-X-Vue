from datetime import date, datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from app.core.auth import Db, current_user
from app.models import Application, Candidate, Communication, Company, CompanyFact, Employment, Job
from app.schemas import (
    ApplicationInput,
    CandidateInput,
    CommunicationInput,
    CompanyInput,
    EmploymentInput,
    FactInput,
    JobInput,
    StatusInput,
)
from app.services.custom_fields import validate_fields
from app.services.records import apply_values, get_record, page_records, save, serialize

router = APIRouter(dependencies=[Depends(current_user)], tags=["workbench"])
Page = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]


@router.get("/dashboard")
def dashboard(db: Db):
    def count(model, *conditions):
        return db.scalar(select(func.count()).select_from(model).where(*conditions))

    return {
        "candidates": count(Candidate),
        "companies": count(Company),
        "open_jobs": count(Job, Job.status == "open"),
        "applications": count(Application),
        "follow_ups": count(
            Communication,
            Communication.follow_up_on <= datetime.now(timezone(timedelta(hours=8))).date(),
        ),
    }


@router.get("/companies")
def companies(db: Db, q: str = "", page: Page = 1, page_size: PageSize = 20):
    conditions = [Company.name.contains(q, autoescape=True)] if q else []
    return page_records(db, Company, conditions, page, page_size)


@router.post("/companies", status_code=201)
def create_company(body: CompanyInput, db: Db):
    return save(db, Company(**body.model_dump()))


@router.get("/companies/{record_id}")
def company(record_id: str, db: Db):
    result = serialize(get_record(db, Company, record_id))
    result["facts"] = [
        serialize(x)
        for x in db.scalars(
            select(CompanyFact)
            .where(CompanyFact.company_id == record_id)
            .order_by(CompanyFact.created_at.desc())
        )
    ]
    return result


@router.patch("/companies/{record_id}")
def update_company(record_id: str, body: CompanyInput, db: Db):
    record = get_record(db, Company, record_id)
    apply_values(record, body.model_dump())
    return save(db, record)


@router.post("/companies/{record_id}/facts", status_code=201)
def create_fact(record_id: str, body: FactInput, db: Db):
    get_record(db, Company, record_id)
    return save(db, CompanyFact(company_id=record_id, **body.model_dump()))


@router.get("/candidates")
def candidates(
    db: Db,
    q: str = "",
    source: str = "",
    contacted_from: date | None = None,
    contacted_to: date | None = None,
    page: Page = 1,
    page_size: PageSize = 20,
):
    if contacted_from and contacted_to and contacted_from > contacted_to:
        raise HTTPException(422, "建联开始日期不能晚于结束日期")
    conditions = []
    if q:
        conditions.append(
            or_(
                *[
                    column.contains(q, autoescape=True)
                    for column in (Candidate.name, Candidate.current_company_name, Candidate.current_title)
                ]
            )
        )
    if source:
        conditions.append(Candidate.resume_source == source)
    if contacted_from:
        conditions.append(Candidate.contacted_on >= contacted_from)
    if contacted_to:
        conditions.append(Candidate.contacted_on <= contacted_to)
    return page_records(db, Candidate, conditions, page, page_size)


def candidate_values(body, db, existing=None):
    values = body.model_dump()
    if body.current_company_id:
        company = get_record(db, Company, body.current_company_id)
        values["current_company_name"] = company.name
    values["custom_fields"] = validate_fields(db, "candidate", body.custom_fields, existing)
    return values


@router.post("/candidates", status_code=201)
def create_candidate(body: CandidateInput, db: Db):
    return save(db, Candidate(**candidate_values(body, db)))


@router.get("/candidates/{record_id}")
def candidate(record_id: str, db: Db):
    result = serialize(get_record(db, Candidate, record_id))
    result["employments"] = [
        serialize(x)
        for x in db.scalars(
            select(Employment)
            .where(Employment.candidate_id == record_id)
            .order_by(Employment.created_at.desc())
        )
    ]
    result["communications"] = [
        serialize(x)
        for x in db.scalars(
            select(Communication)
            .where(Communication.candidate_id == record_id)
            .order_by(Communication.occurred_at.desc().nulls_last(), Communication.created_at.desc())
        )
    ]
    result["applications"] = application_list(db, candidate_id=record_id)
    return result


@router.patch("/candidates/{record_id}")
def update_candidate(record_id: str, body: CandidateInput, db: Db):
    record = get_record(db, Candidate, record_id)
    apply_values(record, candidate_values(body, db, record.custom_fields))
    return save(db, record)


@router.post("/candidates/{record_id}/employments", status_code=201)
def create_employment(record_id: str, body: EmploymentInput, db: Db):
    get_record(db, Candidate, record_id)
    if body.company_id:
        get_record(db, Company, body.company_id)
    return save(db, Employment(candidate_id=record_id, **body.model_dump()))


@router.post("/candidates/{record_id}/communications", status_code=201)
def create_communication(record_id: str, body: CommunicationInput, db: Db):
    get_record(db, Candidate, record_id)
    if body.application_id:
        application = get_record(db, Application, body.application_id)
        if application.candidate_id != record_id:
            raise HTTPException(422, "推荐记录不属于该人才")
    return save(db, Communication(candidate_id=record_id, **body.model_dump()))


@router.get("/jobs")
def jobs(
    db: Db, q: str = "", status: str = "", company_id: str = "", page: Page = 1, page_size: PageSize = 20
):
    conditions = []
    if q:
        companies = select(Company.id).where(Company.name.contains(q, autoescape=True))
        conditions.append(or_(Job.title.contains(q, autoescape=True), Job.company_id.in_(companies)))
    if company_id:
        conditions.append(Job.company_id == company_id)
    if status and status not in ("draft", "open", "paused", "closed"):
        raise HTTPException(422, "招聘状态无效")
    if status:
        conditions.append(Job.status == status)
    result = page_records(db, Job, conditions, page, page_size)
    for item in result["items"]:
        item["company_name"] = get_record(db, Company, item["company_id"]).name
    return result


@router.post("/jobs", status_code=201)
def create_job(body: JobInput, db: Db):
    get_record(db, Company, body.company_id)
    values = body.model_dump()
    values["custom_fields"] = validate_fields(db, "job", body.custom_fields)
    return save(db, Job(**values))


@router.get("/jobs/{record_id}")
def job(record_id: str, db: Db):
    result = serialize(get_record(db, Job, record_id))
    result["company_name"] = get_record(db, Company, result["company_id"]).name
    result["applications"] = application_list(db, job_id=record_id)
    return result


@router.patch("/jobs/{record_id}")
def update_job(record_id: str, body: JobInput, db: Db):
    record = get_record(db, Job, record_id)
    get_record(db, Company, body.company_id)
    values = body.model_dump()
    values["custom_fields"] = validate_fields(db, "job", body.custom_fields, record.custom_fields)
    apply_values(record, values)
    return save(db, record)


def application_list(db, *, candidate_id=None, job_id=None):
    query = (
        select(Application, Candidate.name, Job.title, Company.name)
        .join(Candidate, Application.candidate_id == Candidate.id)
        .join(Job, Application.job_id == Job.id)
        .join(Company, Job.company_id == Company.id)
    )
    if candidate_id:
        query = query.where(Application.candidate_id == candidate_id)
    if job_id:
        query = query.where(Application.job_id == job_id)
    return [
        dict(serialize(item), candidate_name=name, job_title=title, company_name=company)
        for item, name, title, company in db.execute(query.order_by(Application.created_at.desc()))
    ]


@router.post("/applications")
def create_application(body: ApplicationInput, db: Db):
    get_record(db, Candidate, body.candidate_id)
    get_record(db, Job, body.job_id)
    query = select(Application).where(
        Application.candidate_id == body.candidate_id, Application.job_id == body.job_id
    )
    existing = db.scalar(query)
    if existing:
        return serialize(existing)
    try:
        return save(db, Application(**body.model_dump()))
    except IntegrityError:
        db.rollback()
        existing = db.scalar(query)
        if existing:
            return serialize(existing)
        raise


@router.patch("/applications/{record_id}")
def update_application(record_id: str, body: StatusInput, db: Db):
    record = get_record(db, Application, record_id)
    record.status = body.status
    return save(db, record)


@router.get("/candidate-sources")
def candidate_sources(db: Db):
    return list(
        db.scalars(
            select(Candidate.resume_source)
            .where(Candidate.resume_source != "")
            .distinct()
            .order_by(Candidate.resume_source)
        )
    )


def child_record(db, model, parent_field, parent_id, record_id):
    record = get_record(db, model, record_id)
    if getattr(record, parent_field) != parent_id:
        raise HTTPException(404, "记录不存在")
    return record


@router.patch("/candidates/{candidate_id}/employments/{record_id}")
def update_employment(candidate_id: str, record_id: str, body: EmploymentInput, db: Db):
    record = child_record(db, Employment, "candidate_id", candidate_id, record_id)
    if body.company_id:
        get_record(db, Company, body.company_id)
    apply_values(record, body.model_dump())
    return save(db, record)


@router.patch("/candidates/{candidate_id}/communications/{record_id}")
def update_communication(candidate_id: str, record_id: str, body: CommunicationInput, db: Db):
    record = child_record(db, Communication, "candidate_id", candidate_id, record_id)
    if body.application_id and get_record(db, Application, body.application_id).candidate_id != candidate_id:
        raise HTTPException(422, "推荐记录不属于该人才")
    apply_values(record, body.model_dump())
    return save(db, record)


@router.patch("/companies/{company_id}/facts/{record_id}")
def update_fact(company_id: str, record_id: str, body: FactInput, db: Db):
    record = child_record(db, CompanyFact, "company_id", company_id, record_id)
    apply_values(record, body.model_dump())
    return save(db, record)
