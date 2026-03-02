from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import uuid

from app.db.deps import get_db
from app.api.deps_auth import get_current_user
from app.db.models.user import User
from app.db.models.collection import Collection
from app.db.models.document import Document
from app.core.config import get_settings

router = APIRouter(prefix="/documents", tags=["Documents"])

settings = get_settings()


@router.post("/upload/{collection_id}")
def upload_document(
    collection_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.tenant_id == current_user.tenant_id
    ).one_or_none()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    storage_root = settings.file_storage_path
    storage_root.mkdir(parents=True, exist_ok=True)

    unique_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = storage_root / unique_name

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    document = Document(
        collection_id=collection_id,
        tenant_id=current_user.tenant_id,
        filename=file.filename,
        content_type=file.content_type,
        file_path=str(file_path),
        uploaded_by=current_user.id,
        status="uploaded",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "document_id": document.id,
        "filename": document.filename,
        "status": document.status,
    }