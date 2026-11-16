"""Photo endpoints (ADR-0014; FR-B-01, FR-B-11, NFR-S-06; plan item M4).

POST /items/{id}/photos (owner) and POST /transactions/{id}/photos (party; purpose HANDOVER,
RETURN or DISPUTE) take one multipart file each. GET /attachments/{id} returns a short-lived signed
link for someone allowed to see the photo; GET /files/{key} serves it when storage is the local
disk. Wrong type or size: 422 (TC-85). No storage configured: 503, and the checklist goes on alone.
"""

from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Connection, Engine

from app.api import schemas
from app.api.deps import current_actor, get_engine
from app.config.settings import get_settings
from app.domain.lifecycle.service import Actor
from app.domain.uploads.service import AttachmentService
from app.domain.uploads.storage import LocalDiskStorage, StoragePort, UnavailableStorage
from app.infra.db.attachments import PostgresAttachmentStore

router = APIRouter(prefix="/api/v1")
MIME = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp"}


class ItemPhotoForm(BaseModel):
    """Multipart body: the file and nothing else. Unknown fields are refused (TC-60)."""

    model_config = ConfigDict(extra="forbid")
    file: UploadFile


class LoanPhotoForm(ItemPhotoForm):
    purpose: Literal["HANDOVER", "RETURN", "DISPUTE"]


def storage() -> StoragePort:
    settings = get_settings()
    if settings.storage_dir and settings.jwt_secret:
        return LocalDiskStorage(Path(settings.storage_dir), settings.jwt_secret)
    return UnavailableStorage()


def _service(conn: Connection) -> AttachmentService:
    settings = get_settings()
    return AttachmentService(
        PostgresAttachmentStore(conn),
        storage(),
        max_bytes=settings.upload_max_bytes,
        url_ttl_seconds=settings.photo_url_ttl_seconds,
    )


async def _read(file: UploadFile) -> bytes:
    """Read at most one byte over the limit, so a huge upload is refused without being held."""
    return await file.read(get_settings().upload_max_bytes + 1)


@router.post("/items/{item_id}/photos", response_model=schemas.AttachmentOut, status_code=201)
async def add_item_photo(
    item_id: UUID,
    form: Annotated[ItemPhotoForm, Form()],
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.AttachmentOut:
    data = await _read(form.file)
    with engine.begin() as conn:
        saved = _service(conn).add_item_photo(actor.user_id, item_id, data)
    return schemas.AttachmentOut(**saved)


@router.post("/transactions/{txn_id}/photos", response_model=schemas.AttachmentOut, status_code=201)
async def add_loan_photo(
    txn_id: UUID,
    form: Annotated[LoanPhotoForm, Form()],
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.AttachmentOut:
    data = await _read(form.file)
    with engine.begin() as conn:
        saved = _service(conn).add_loan_photo(actor.user_id, txn_id, form.purpose, data)
    return schemas.AttachmentOut(**saved)


@router.get("/attachments/{attachment_id}", response_model=schemas.AttachmentUrlOut)
def attachment_url(
    attachment_id: UUID,
    actor: Actor = Depends(current_actor),
    engine: Engine = Depends(get_engine),
) -> schemas.AttachmentUrlOut:
    with engine.connect() as conn:
        url, exp = _service(conn).url(actor.user_id, actor.platform_role, attachment_id)
    return schemas.AttachmentUrlOut(url=url, expires_at=exp)


@router.get("/files/{key}", include_in_schema=False)
def serve_file(key: str, exp: int = Query(...), sig: str = Query(...)) -> Response:
    """Local-disk storage only: the signature and expiry are the authorisation."""
    store = storage()
    if not isinstance(store, LocalDiskStorage) or not store.verify(key, exp, sig):
        raise HTTPException(status_code=404, detail="not found")
    try:
        data = store.get(key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="not found") from exc
    media = MIME.get(key.rsplit(".", 1)[-1], "application/octet-stream")
    return Response(
        content=data, media_type=media, headers={"Cache-Control": "private, max-age=60"}
    )
