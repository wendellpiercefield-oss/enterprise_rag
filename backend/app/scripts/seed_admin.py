from app.db import base_imports  # IMPORTANT: registers models
from app.db.session import SessionLocal
from app.db.models.user import User
from app.core.security import hash_password


def main():
    db = SessionLocal()
    try:
        email = "admin@whitedrive.local"
        password = "ChangeMeNow!"
        tenant_id = 1  # WhiteDrive tenant you created

        existing = db.query(User).filter(User.email == email).one_or_none()
        if existing:
            print("Admin already exists:", existing.email)
            return

        user = User(
            email=email,
            password_hash=hash_password(password),
            role="admin",
            tenant_id=tenant_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        print("Created admin:", user.email, "password:", password)
    finally:
        db.close()

if __name__ == "__main__":
    main()