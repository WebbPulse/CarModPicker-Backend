from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

# Get settings using the function (which could be overridden in tests)
settings = get_settings()

# Create the SQLAlchemy engine
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
