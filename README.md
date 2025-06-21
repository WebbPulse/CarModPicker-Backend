#WIP README


Useful commands:
- docker compose up -d
    - to build the backend, the prod db, and the test db for unit tests
- alembic upgrade head
    - to get db schema up to date
- pytest 
    - to trigger unit tests
- uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    - To start server outside of docker


Prerequisites:
- .env
- .env.test
- k8s postgres secrets
- k8s backend secrets
- for docker debug with backend, configure a docker network with 'docker network create carmodpicker_network' 
