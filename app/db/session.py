from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..core.config import settings

# Create the SQLAlchemy engine
# connect_args is specific to SQLite, remove or adjust for PostgreSQL if needed
# For PostgreSQL, you might not need connect_args unless dealing with specific SSL modes etc.
engine = create_engine(
    settings.DATABASE_URL,
    # pool_pre_ping=True # Optional: helps manage connections
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()