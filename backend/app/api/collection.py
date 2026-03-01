from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.db.models.collection import Collection
from app.schemas.collection import CollectionCreate, CollectionRead
from app.api.deps_auth import get_current_user
from app.db.models.user import User
from app.db.models.collection_member import CollectionMember
from app.schemas.collection_member import CollectionMemberCreate
from app.api.deps_auth import require_collection_admin

router = APIRouter(prefix="/collections", tags=["Collections"])


@router.post("/", response_model=CollectionRead)
def create_collection(
    payload: CollectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    collection = Collection(
        name=payload.name,
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
    )

    db.add(collection)
    db.commit()
    db.refresh(collection)

    # Auto-add creator as admin member
    membership = CollectionMember(
        collection_id=collection.id,
        user_id=current_user.id,
        role="admin",
    )

    db.add(membership)
    db.commit()

    return collection


@router.post("/{collection_id}/members")
def add_member(
    collection_id: int,
    payload: CollectionMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_collection_admin),
):
    membership = CollectionMember(
        collection_id=collection_id,
        user_id=payload.user_id,
        role=payload.role,
    )

    db.add(membership)
    db.commit()

    return {"status": "member added"}

@router.get("/", response_model=list[CollectionRead])
def list_collections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Collection)
        .join(CollectionMember, Collection.id == CollectionMember.collection_id)
        .filter(
            CollectionMember.user_id == current_user.id,
            Collection.tenant_id == current_user.tenant_id,
        )
        .all()
    )
