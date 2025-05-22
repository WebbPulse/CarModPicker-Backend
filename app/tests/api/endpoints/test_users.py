from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # Import Session if direct db interaction is needed, though often not for API tests
from app.api.schemas.user import UserRead, UserCreate, UserUpdate
from app.core.config import settings # For API prefixes or other settings if needed

# Helper function to get auth headers after creating/logging in a user
# This assumes your /token endpoint and user creation are working.
# For robust testing, auth tests should be separate, but this helps for testing protected user endpoints.
def get_auth_headers(client: TestClient, username: str, password: str) -> dict:
    login_data = {"username": username, "password": password}
    response = client.post(f"{settings.API_STR}/token", data=login_data) # Assuming /token is at root or adjust path
    if response.status_code != 200:
        # Fallback: try token endpoint without API_V1_STR if the above fails
        response = client.post(f"{settings.API_STR}/token", data=login_data)
        if response.status_code != 200:
            raise Exception(f"Failed to log in user {username} to get token. Status: {response.status_code}, Detail: {response.text}")
    
    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}

def test_create_user(client: TestClient):
    user_data = {
        "username": "testuser1",
        "email": "testuser1@example.com",
        "password": "password123",
        "first_name": "Test",
        "last_name": "User1"
    }
    response = client.post(f"{settings.API_STR}/users/", json=user_data)
    assert response.status_code == 200, response.text
    created_user = response.json()
    assert created_user["username"] == user_data["username"]
    assert created_user["email"] == user_data["email"]
    assert created_user["first_name"] == user_data["first_name"]
    assert created_user["last_name"] == user_data["last_name"]
    assert "id" in created_user
    assert created_user["disabled"] is False

def test_create_user_duplicate_username(client: TestClient):
    user_data1 = {"username": "dupuser", "email": "dupuser1@example.com", "password": "password123"}
    client.post(f"{settings.API_STR}/users/", json=user_data1) # Create first user

    user_data2 = {"username": "dupuser", "email": "dupuser2@example.com", "password": "password456"}
    response = client.post(f"{settings.API_STR}/users/", json=user_data2)
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"

def test_create_user_duplicate_email(client: TestClient):
    user_data1 = {"username": "emailuser1", "email": "dupemail@example.com", "password": "password123"}
    client.post(f"{settings.API_STR}/users/", json=user_data1) # Create first user

    user_data2 = {"username": "emailuser2", "email": "dupemail@example.com", "password": "password456"}
    response = client.post(f"{settings.API_STR}/users/", json=user_data2)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_read_user(client: TestClient):
    user_data = {"username": "readuser", "email": "readuser@example.com", "password": "password123"}
    create_response = client.post(f"{settings.API_STR}/users/", json=user_data)
    user_id = create_response.json()["id"]

    response = client.get(f"{settings.API_STR}/users/{user_id}")
    assert response.status_code == 200, response.text
    read_user_data = response.json()
    assert read_user_data["username"] == user_data["username"]
    assert read_user_data["email"] == user_data["email"]
    assert read_user_data["id"] == user_id

def test_read_nonexistent_user(client: TestClient):
    response = client.get(f"{settings.API_STR}/users/999999") # Assuming this ID won't exist
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

def test_update_own_user(client: TestClient):
    # Create user
    username = "updateuser"
    password = "password123"
    user_data_initial = {
        "username": username,
        "email": "updateuser@example.com",
        "password": password,
        "first_name": "InitialFirst"
    }
    create_response = client.post(f"{settings.API_STR}/users/", json=user_data_initial)
    assert create_response.status_code == 200, create_response.text
    user_id = create_response.json()["id"]

    # Get auth token
    auth_headers = get_auth_headers(client, username, password)

    # Update user
    update_payload = {"first_name": "UpdatedFirst", "email": "updatedemail@example.com"}
    response = client.put(f"{settings.API_STR}/users/{user_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 200, response.text
    updated_user = response.json()
    assert updated_user["first_name"] == "UpdatedFirst"
    assert updated_user["email"] == "updatedemail@example.com"
    assert updated_user["username"] == username # Username should not change unless specified

def test_update_another_user_forbidden(client: TestClient):
    # Create user A
    user_a_data = {"username": "userA_updater", "email": "usera_updater@example.com", "password": "passwordA"}
    client.post(f"{settings.API_STR}/users/", json=user_a_data)
    auth_headers_a = get_auth_headers(client, user_a_data["username"], user_a_data["password"])

    # Create user B
    user_b_data = {"username": "userB_victim_update", "email": "userb_victim@example.com", "password": "passwordB"}
    response_b = client.post(f"{settings.API_STR}/users/", json=user_b_data)
    user_b_id = response_b.json()["id"]

    # User A tries to update User B
    update_payload = {"first_name": "MaliciousUpdate"}
    response = client.put(f"{settings.API_STR}/users/{user_b_id}", json=update_payload, headers=auth_headers_a)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to update this user"

def test_delete_own_user(client: TestClient):
    # Create user
    username = "deleteuser"
    password = "password123"
    user_data_initial = {"username": username, "email": "deleteuser@example.com", "password": password}
    create_response = client.post(f"{settings.API_STR}/users/", json=user_data_initial)
    user_id = create_response.json()["id"]

    # Get auth token
    auth_headers = get_auth_headers(client, username, password)

    # Delete user
    response = client.delete(f"{settings.API_STR}/users/{user_id}", headers=auth_headers)
    assert response.status_code == 200, response.text
    deleted_user_data = response.json()
    assert deleted_user_data["id"] == user_id
    assert deleted_user_data["username"] == username

    # Verify user is deleted (e.g., by trying to read or login)
    get_response = client.get(f"{settings.API_STR}/users/{user_id}")
    assert get_response.status_code == 404 # User should not be found

    login_response = client.post(f"{settings.API_STR}/token", data={"username": username, "password": password})
    assert login_response.status_code == 401 # Should not be able to login

def test_delete_another_user_forbidden(client: TestClient):
    # Create user A (deleter)
    user_a_data = {"username": "userA_deleter", "email": "usera_deleter@example.com", "password": "passwordA"}
    client.post(f"{settings.API_STR}/users/", json=user_a_data)
    auth_headers_a = get_auth_headers(client, user_a_data["username"], user_a_data["password"])

    # Create user B (victim)
    user_b_data = {"username": "userB_victim_delete", "email": "userb_victim_delete@example.com", "password": "passwordB"}
    response_b = client.post(f"{settings.API_STR}/users/", json=user_b_data)
    user_b_id = response_b.json()["id"]

    # User A tries to delete User B
    response = client.delete(f"{settings.API_STR}/users/{user_b_id}", headers=auth_headers_a)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to delete this user"

def test_read_users_me_success(client: TestClient):
    username = "me_user"
    password = "password123"
    email = "me_user@example.com"
    user_data = {"username": username, "email": email, "password": password, "first_name": "Me", "last_name": "User"}
    
    create_response = client.post(f"{settings.API_STR}/users/", json=user_data)
    assert create_response.status_code == 200
    user_id = create_response.json()["id"]

    login_data = {"username": username, "password": password}
    token_response = client.post(f"{settings.API_STR}/token", data=login_data)
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"{settings.API_STR}/users/me", headers=headers) # Endpoint is /users/me
    assert response.status_code == 200, response.text
    current_user = response.json()
    assert current_user["username"] == username
    assert current_user["email"] == email
    assert current_user["id"] == user_id
    assert current_user["first_name"] == "Me"
    assert current_user["disabled"] is False

def test_read_users_me_invalid_token(client: TestClient):
    headers = {"Authorization": "Bearer invalidtoken"}
    response = client.get(f"{settings.API_STR}/users/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

def test_read_users_me_no_token(client: TestClient):
    response = client.get(f"{settings.API_STR}/users/me") # No auth header
    assert response.status_code == 401 # FastAPI's default for missing OAuth2 token
    assert response.json()["detail"] == "Not authenticated" # Or "Missing Authorization Header" depending on FastAPI version/setup