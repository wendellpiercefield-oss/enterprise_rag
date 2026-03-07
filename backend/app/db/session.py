from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.db.base import Base

# Import models so SQLAlchemy metadata loads them
from app.db.models import tenant
from app.db.models import user
from app.db.models import collection
from app.db.models import document

settings = get_settings()

engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)