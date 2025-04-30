from fastapi import FastAPI
from core.config import settings
from api.endpoints import items
# Create database tables (For PoC, use Alembic for production)
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG
)

app.include_router(items.router, prefix="/items", tags=["items"])

@app.get("/")
def read_root():
    return {"Hello": "World"}
    


