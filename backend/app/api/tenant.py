from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.schemas.tenant import TenantCreate, TenantRead
from app.services.tenant_service import create_tenant

router = APIRouter(prefix="/tenants", tags=["Tenants"])

@router.post("/", response_model=TenantRead)
def create_tenant_endpoint(
    payload: TenantCreate,
    db: Session = Depends(get_db),
):
    return create_tenant(db, payload.name)