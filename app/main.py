from fastapi import FastAPI
from core.config import settings
from api.endpoints import items
from api.endpoints import auth
from api.endpoints import users
# Create database tables (For PoC, use Alembic for production)
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG
)

app.include_router(items.router, prefix="/items", tags=["items"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(auth.router, tags=["auth"]) # Add auth router (prefix depends on tokenUrl)

@app.get("/")
def read_root():
    return {"Hello": "World"}
    


