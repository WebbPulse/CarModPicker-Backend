WIP README

To start server outside of docker: 
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Local debug steps if no DB volume exists:
- docker compose up -d
- alembic upgrade head
