import hashlib
import json
import math
import re
from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select

from app.models import CustomFieldDefinition
from app.services.records import serialize

RESUME_LINK_ID = "00000000-0000-4000-8000-000000000001"


def builtin_fields(entity):
    if entity != "candidate":
        return []
    timestamp = datetime(2026, 10, 16, tzinfo=timezone.utc)
    # Transient definition: values use the existing JSON column; no database writes or DDL.
    return [
        CustomFieldDefinition(
            id=RESUME_LINK_ID,
            key="resume_link",
            entity_type="candidate",
            label="简历链接",
            value_type="text",
            options=[],
            description="保存简历或候选人页面的完整链接",
            required=False,
            enabled=True,
            position=0,
            version=1,
            created_at=timestamp,
            updated_at=timestamp,
        )
    ]


def definitions(db, entity):
    return builtin_fields(entity) + list(
        db.scalars(
            select(CustomFieldDefinition)
            .where(CustomFieldDefinition.entity_type == entity)
            .order_by(CustomFieldDefinition.position, CustomFieldDefinition.created_at)
        ).all()
    )


def snapshot(db):
    values = [serialize(x) for x in definitions(db, "candidate")]
    return hashlib.sha256(json.dumps(values, sort_keys=True, default=str).encode()).hexdigest()


def validate_fields(db, entity, supplied, existing=None, field_definitions=None):
    result = dict(existing or {})
    fields = {
        item.key: item
        for item in (field_definitions if field_definitions is not None else definitions(db, entity))
    }
    for key, value in supplied.items():
        field = fields.get(key)
        if not field:
            if key in result and result[key] == value:
                continue
            raise HTTPException(422, "存在未定义的自定义字段")
        if not field.enabled:
            if value != result.get(key):
                raise HTTPException(422, f"{field.label} 已停用，不能修改历史值")
            continue
        valid = value is None or value == ""
        if not valid:
            if field.value_type == "text":
                valid = isinstance(value, str) and len(value) <= 2000
            elif field.value_type == "number":
                valid = type(value) in (int, float) and math.isfinite(value)
            elif field.value_type == "select":
                valid = isinstance(value, str) and value in [x["value"] for x in field.options]
            elif field.value_type == "date":
                try:
                    valid = isinstance(value, str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))
                    if valid:
                        date.fromisoformat(value)
                except ValueError:
                    valid = False
        if not valid:
            raise HTTPException(422, f"{field.label} 的值不符合字段类型或选项")
        result[key] = value
    for field in fields.values():
        if field.enabled and field.required and result.get(field.key) in (None, ""):
            raise HTTPException(422, f"请补充必填字段：{field.label}")
    return result
