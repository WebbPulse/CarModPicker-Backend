from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.api.schemas.user import UserRead
from app.api.models.user import User as DBUser # For direct DB manipulation if needed

# Helper to create a user directly in the DB for testing login
# This is an alternative to calling the /users/ endpoint if you want to bypass API validation for setup
from app.api.dependencies.auth import get_password_hash

def create_test_user_direct_db(db: Session, username: str, email: str, password: str, disabled: bool = False) -> DBUser:
    hashed_password = get_password_hash(password)
    db_user = DBUser(
        username=username,
        email=email,
        hashed_password=hashed_password,
        disabled=disabled
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def test_login_for_access_token_success(client: TestClient, db_session: Session):
    # Create a user first (either via API or directly in DB for isolated auth test)
    username = "auth_test_user"
    password = "auth_test_password"
    email = "auth_test@example.com"
    
    # Using the API to create the user to ensure it's in a valid state
    user_data = {"username": username, "email": email, "password": password}
    response = client.post(f"{settings.API_STR}/users/", json=user_data)
    assert response.status_code == 200, f"Failed to create user for auth test: {response.text}"

    login_data = {"username": username, "password": password}
    response = client.post(f"{settings.API_STR}/token", data=login_data) # tokenUrl is relative to base
    assert response.status_code == 200, response.text
    token = response.json()
    assert "access_token" in token
    assert token["token_type"] == "bearer"

def test_login_for_access_token_incorrect_username(client: TestClient):
    login_data = {"username": "wronguser", "password": "password123"}
    response = client.post(f"{settings.API_STR}/token", data=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_login_for_access_token_incorrect_password(client: TestClient, db_session: Session):
    username = "auth_test_user_wrong_pass"
    password = "correct_password"
    email = "auth_test_wrong_pass@example.com"
    
    user_data = {"username": username, "email": email, "password": password}
    client.post(f"{settings.API_STR}/users/", json=user_data) # Create the user

    login_data = {"username": username, "password": "wrong_password"}
    response = client.post(f"{settings.API_STR}/token", data=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_login_for_access_token_disabled_user(client: TestClient, db_session: Session):
    username = "disabled_user"
    password = "password123"
    email = "disabled@example.com"

    # Create user via API
    user_data = {"username": username, "email": email, "password": password}
    create_response = client.post(f"{settings.API_STR}/users/", json=user_data)
    assert create_response.status_code == 200
    user_id = create_response.json()["id"]

    # Log in as the user to get a token to disable them
    # (or create another admin user to do this, for simplicity using the same user's token)
    login_data_for_token = {"username": username, "password": password}
    token_response = client.post(f"{settings.API_STR}/token", data=login_data_for_token)
    assert token_response.status_code == 200
    auth_token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Disable the user via API
    update_payload = {"disabled": True}
    update_response = client.put(f"{settings.API_STR}/users/{user_id}", json=update_payload, headers=headers)
    assert update_response.status_code == 200, f"Failed to disable user: {update_response.text}"
    assert update_response.json()["disabled"] is True
    
    # Attempt to login as the now disabled user
    login_data = {"username": username, "password": password}
    response = client.post(f"{settings.API_STR}/token", data=login_data)
    assert response.status_code == 400, response.text # As per your auth.py logic
    assert response.json()["detail"] == "Inactive user"


