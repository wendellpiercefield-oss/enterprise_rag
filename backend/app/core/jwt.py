from datetime import datetime, timedelta, timezone
from jose import jwt

from app.core.config import get_settings

settings = get_settings()

def create_access_token(sub: str, role: str, tenant_id: int) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.access_token_exp_minutes)

    payload = {
        "sub": sub,
        "role": role,
        "tenant_id": tenant_id,
        "iat": int(now.timestamp()),
        "exp": exp,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)