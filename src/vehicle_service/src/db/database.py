from utils.db import Base, get_session_factory
from config import settings

SessionLocal = get_session_factory(settings.database_url)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
