from fastapi import HTTPException
from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session


def get_record(db: Session, model, record_id):
    value = db.get(model, record_id)
    if value is None:
        raise HTTPException(404, "记录不存在")
    return value


def serialize(record):
    return {column.key: getattr(record, column.key) for column in inspect(record).mapper.column_attrs}


def page_records(db, model, conditions, page, page_size):
    query = select(model).where(*conditions)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = db.scalars(
        query.order_by(model.updated_at.desc(), model.id).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {
        "items": [serialize(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def save(db, record):
    db.add(record)
    db.commit()
    db.refresh(record)
    return serialize(record)


def apply_values(record, values):
    for name, value in values.items():
        setattr(record, name, value)
    if hasattr(record, "version"):
        record.version += 1
