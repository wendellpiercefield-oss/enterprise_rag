from sqlalchemy.orm import Session
from app.db.models.tenant import Tenant

def create_tenant(db: Session, name: str) -> Tenant:
    tenant = Tenant(name=name)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant