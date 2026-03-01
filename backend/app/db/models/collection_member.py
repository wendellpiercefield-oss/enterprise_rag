from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class CollectionMember(Base):
    __tablename__ = "collection_members"

    id: Mapped[int] = mapped_column(primary_key=True)

    collection_id: Mapped[int] = mapped_column(
        ForeignKey("collections.id"), nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    role: Mapped[str] = mapped_column(String(50), default="member")