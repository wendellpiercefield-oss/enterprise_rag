from app.db import base_imports
from app.db.session import SessionLocal
from app.db.models.user import User
from app.core.security import hash_password

def main():
    db = SessionLocal()

    user = User(
        email="user@whitedrive.local",
        password_hash=hash_password("User123!"),
        role="user",
        tenant_id=1,
    )

    db.add(user)
    db.commit()

    print("Created user: user@whitedrive.local password: User123!")

if __name__ == "__main__":
    main()