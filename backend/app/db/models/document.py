from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=False, index=True)

    filename = Column(String(512), nullable=False)
    content_type = Column(String(255), nullable=True)

    file_path = Column(Text, nullable=False)

    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    status = Column(String(32), nullable=False, default="uploaded", index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)