import csv
import hashlib
import io
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, Query, Request, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy import select

from app.core.auth import CurrentUser, Db
from app.models import ImportBatch, ImportRow
from app.schemas.imports import CommitInput, PreviewInput, RowInput
from app.services import imports as service
from app.services.records import page_records, serialize

router = APIRouter(prefix="/imports", tags=["imports"])
Page = Annotated[int, Query(ge=1)]
Size = Annotated[int, Query(ge=1, le=100)]


@router.get("/template")
def template(user: CurrentUser):
    return FileResponse(
        Path(__file__).resolve().parents[1] / "assets" / "candidate-import-template.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="hunter-talent-template.xlsx",
    )


@router.post("/upload", status_code=201)
async def upload(request: Request, db: Db, user: CurrentUser, file: Annotated[UploadFile, File()]):
    name = (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    file_format = Path(name).suffix.lower().lstrip(".")
    if file_format not in ("xlsx", "csv") or len(name) > 255:
        service.fail("请选择 .xlsx 或 UTF-8 CSV；旧 .xls / 宏文件需另存为 .xlsx")
    data = await file.read(service.FILE_LIMIT + 1)
    sheets = service.decode_file(data, file_format)
    checksum = hashlib.sha256(data).hexdigest()
    previous = db.scalars(
        select(ImportBatch.id).where(ImportBatch.created_by == user.id, ImportBatch.checksum == checksum)
    ).all()
    key = str(uuid4())
    root = service.import_root(request)
    root.mkdir(parents=True, exist_ok=True)
    with (root / key).open("xb") as stream:
        stream.write(data)
    batch = ImportBatch(
        created_by=user.id,
        original_name=name,
        file_format=file_format,
        checksum=checksum,
        storage_key=key,
        size=len(data),
        sheets=sheets,
    )
    db.add(batch)
    db.commit()
    return {**serialize(batch), "previous_batches": list(previous)}


@router.get("")
def batches(db: Db, user: CurrentUser, page: Page = 1, page_size: Size = 20):
    return page_records(db, ImportBatch, [ImportBatch.created_by == user.id], page, page_size)


@router.get("/{record_id}")
def batch_detail(record_id: str, db: Db, user: CurrentUser):
    return serialize(service.owned_batch(db, record_id, user.id))


@router.get("/{record_id}/file")
def original(record_id: str, request: Request, db: Db, user: CurrentUser):
    batch = service.owned_batch(db, record_id, user.id)
    return FileResponse(service.import_root(request) / batch.storage_key, filename=batch.original_name)


@router.post("/{record_id}/preview")
def preview(record_id: str, body: PreviewInput, request: Request, db: Db, user: CurrentUser):
    user_id = user.id
    service.write_transaction(db)
    batch = service.owned_batch(db, record_id, user_id, True)
    return service.preview(db, batch, body, service.import_root(request))


@router.get("/{record_id}/rows")
def rows(record_id: str, db: Db, user: CurrentUser, page: Page = 1, page_size: Size = 20):
    batch = service.owned_batch(db, record_id, user.id)
    return page_records(
        db,
        ImportRow,
        [
            ImportRow.batch_id == batch.id,
            ImportRow.sheet_name == batch.sheet_name,
            ImportRow.row_number > batch.header_row,
        ],
        page,
        page_size,
        order_by=(ImportRow.row_number,),
    )


@router.patch("/{record_id}/rows/{row_id}")
def update_row(record_id: str, row_id: str, body: RowInput, db: Db, user: CurrentUser):
    user_id = user.id
    service.write_transaction(db)
    batch = service.owned_batch(db, record_id, user_id, True)
    return service.edit_row(db, batch, row_id, body)


@router.post("/{record_id}/commit")
def commit(record_id: str, body: CommitInput, db: Db, user: CurrentUser):
    user_id = user.id
    service.write_transaction(db)
    batch = service.owned_batch(db, record_id, user_id, True)
    return service.commit(db, batch, body)


@router.post("/{record_id}/cancel")
def cancel(record_id: str, db: Db, user: CurrentUser):
    user_id = user.id
    service.write_transaction(db)
    batch = service.owned_batch(db, record_id, user_id, True)
    service.ensure_editable(batch)
    batch.status = "cancelled"
    db.commit()
    return serialize(batch)


@router.get("/{record_id}/errors")
def errors(record_id: str, db: Db, user: CurrentUser):
    batch = service.owned_batch(db, record_id, user.id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["工作表", "原行号", "字段/列", "原因", "原文"])
    for row in service.active_rows(db, batch):
        for item in row.errors + row.warnings:
            column = item["column"]
            raw = (
                row.original[int(column)]["value"]
                if column.isdigit() and int(column) < len(row.original)
                else ""
            )
            writer.writerow(
                [service.safe_csv(x) for x in [row.sheet_name, row.row_number, column, item["message"], raw]]
            )
    return Response(
        output.getvalue().encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="hunter-import-errors.csv"'},
    )
