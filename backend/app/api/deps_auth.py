from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.deps import get_db
from app.db.models.user import User
from app.db.models.collection_member import CollectionMember
from app.db.models.collection import Collection

settings = get_settings()
security = HTTPBearer()


# -----------------------------
# 1️⃣ Define get_current_user FIRST
# -----------------------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == int(user_id)).one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# -----------------------------
# 2️⃣ THEN define require_collection_admin
# -----------------------------
def require_collection_admin(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    membership = (
        db.query(CollectionMember)
        .join(Collection)
        .filter(
            CollectionMember.collection_id == collection_id,
            CollectionMember.user_id == current_user.id,
            Collection.tenant_id == current_user.tenant_id,
            CollectionMember.role == "admin",
        )
        .one_or_none()
    )

    if not membership:
        raise HTTPException(status_code=403, detail="Not collection admin")

    return current_user