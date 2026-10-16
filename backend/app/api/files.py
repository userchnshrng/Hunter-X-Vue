import hashlib
import io
import zipfile
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from app.core.auth import Db, current_user
from app.models import Candidate, FileAsset, Job
from app.services.records import get_record, save

router = APIRouter(prefix="/files", dependencies=[Depends(current_user)], tags=["files"])
LIMIT = 20 * 1024 * 1024


def check_type(name, data):
    suffix = Path(name).suffix.lower()
    if suffix == ".pdf" and data.startswith(b"%PDF-"):
        return "application/pdf"
    if suffix == ".png" and data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if suffix in (".jpg", ".jpeg") and data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if suffix == ".docx" and data.startswith(b"PK"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                if sum(item.file_size for item in archive.infolist()) > 100 * 1024 * 1024:
                    raise HTTPException(422, "Word 文件展开后过大")
                if "word/document.xml" in archive.namelist():
                    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        except zipfile.BadZipFile:
            pass
    if suffix == ".txt":
        for encoding in ("utf-8-sig", "gb18030", "utf-16"):
            try:
                text = data.decode(encoding)
                if "\x00" not in text:
                    return "text/plain"
            except UnicodeError:
                continue
    raise HTTPException(422, "文件内容与格式不匹配；当前附件支持 TXT、PDF、DOCX、PNG、JPEG")


@router.post("/{owner_type}/{owner_id}", status_code=201)
async def upload(
    owner_type: Literal["candidate", "job"],
    owner_id: str,
    request: Request,
    db: Db,
    file: Annotated[UploadFile, File()],
):
    get_record(db, Candidate if owner_type == "candidate" else Job, owner_id)
    data = await file.read(LIMIT + 1)
    if not data or len(data) > LIMIT:
        raise HTTPException(413, "附件必须非空且不超过 20 MB")
    name = (file.filename or "attachment").replace("\\", "/").rsplit("/", 1)[-1]
    if len(name) > 255:
        raise HTTPException(422, "文件名过长")
    media_type = check_type(name, data)
    key = str(uuid4())
    root = request.app.state.settings.upload_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    with (root / key).open("xb") as stream:
        stream.write(data)
    return save(
        db,
        FileAsset(
            owner_type=owner_type,
            owner_id=owner_id,
            original_name=name,
            media_type=media_type,
            size=len(data),
            checksum=hashlib.sha256(data).hexdigest(),
            storage_key=key,
        ),
    )


@router.get("/owners/{owner_type}/{owner_id}")
def list_files(owner_type: Literal["candidate", "job"], owner_id: str, db: Db):
    from sqlalchemy import select

    from app.services.records import serialize

    get_record(db, Candidate if owner_type == "candidate" else Job, owner_id)
    return [
        serialize(item)
        for item in db.scalars(
            select(FileAsset)
            .where(FileAsset.owner_type == owner_type, FileAsset.owner_id == owner_id)
            .order_by(FileAsset.created_at.desc())
        )
    ]


@router.get("/{file_id}/download")
def download(file_id: str, request: Request, db: Db):
    asset = get_record(db, FileAsset, file_id)
    root = request.app.state.settings.upload_root.resolve()
    path = (root / asset.storage_key).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise HTTPException(404, "附件不存在")
    return FileResponse(path, filename=asset.original_name, media_type="application/octet-stream")
