from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update

from app.core.auth import CurrentUser, Db, current_user
from app.models import CustomFieldDefinition
from app.schemas.fields import Entity, FieldInput, FieldUpdate
from app.services.custom_fields import RESUME_LINK_ID, definitions
from app.services.records import get_record, save, serialize

router = APIRouter(prefix="/custom-fields", dependencies=[Depends(current_user)], tags=["fields"])


def admin(user):
    if user.role != "admin":
        raise HTTPException(403, "只有管理员可以维护字段定义")


@router.get("")
def list_fields(entity_type: Entity, db: Db):
    return [
        {**serialize(item), "builtin": item.id == RESUME_LINK_ID} for item in definitions(db, entity_type)
    ]


@router.post("", status_code=201)
def create_field(body: FieldInput, db: Db, user: CurrentUser):
    admin(user)
    if len([item for item in definitions(db, body.entity_type) if item.id != RESUME_LINK_ID]) >= 50:
        raise HTTPException(422, "每类最多设置 50 个字段")
    return save(db, CustomFieldDefinition(key=f"field_{uuid4().hex}", **body.model_dump()))


@router.patch("/{record_id}")
def update_field(record_id: str, body: FieldUpdate, db: Db, user: CurrentUser):
    admin(user)
    if record_id == RESUME_LINK_ID:
        raise HTTPException(422, "简历链接是固定字段，其值可在人才详情维护，定义不能更改")
    field = get_record(db, CustomFieldDefinition, record_id)
    if body.entity_type != field.entity_type or body.value_type != field.value_type:
        raise HTTPException(422, "字段归属和类型创建后不能更改，请新建字段")
    if field.version != body.version:
        raise HTTPException(409, "字段已被更新，请刷新后重试")
    if not {x["value"] for x in field.options}.issubset({x.value for x in body.options}):
        raise HTTPException(422, "历史选项不能移除，可修改显示名或追加选项")
    result = db.execute(
        update(CustomFieldDefinition)
        .where(CustomFieldDefinition.id == record_id, CustomFieldDefinition.version == body.version)
        .values(**body.model_dump(exclude={"version"}), version=body.version + 1)
    )
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "字段已被更新，请刷新后重试")
    db.commit()
    return serialize(get_record(db, CustomFieldDefinition, record_id))
