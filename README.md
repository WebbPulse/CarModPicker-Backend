To start server outside of docker: 
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Local debug steps if no DB volume exists:
- docker compose up -d
- alembic upgrade head


