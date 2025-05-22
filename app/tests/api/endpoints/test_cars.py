from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.api.schemas.car import CarRead, CarCreate, CarUpdate
from app.api.models.user import User as DBUser

# Helper function to create a user and get auth headers
# This could be imported from a shared test utility module if you have one
# For now, adapting the one from your test_users.py
def create_user_and_get_headers(client: TestClient, username_suffix: str, password_suffix: str) -> tuple[dict, int]:
    username = f"car_test_user_{username_suffix}"
    email = f"car_test_user_{username_suffix}@example.com"
    password = f"password_{password_suffix}"
    
    user_data = {
        "username": username,
        "email": email,
        "password": password,
        "first_name": "CarTest",
        "last_name": username_suffix.capitalize()
    }
    # Ensure user creation endpoint is correct
    response = client.post(f"{settings.API_STR}/users/", json=user_data)
    if response.status_code != 200 and response.status_code != 400: # Allow if user already exists from previous run
        raise Exception(f"Failed to create user {username} for car tests. Status: {response.status_code}, Detail: {response.text}")
    
    user_id = -1
    if response.status_code == 200:
        user_id = response.json()["id"]
    elif response.status_code == 400: # User might already exist, try to get ID by logging in
        # This part is tricky without querying DB directly or having a get_user_by_username endpoint
        # For simplicity, we'll assume tests run in a clean state or user creation is idempotent for testing
        # If user already exists, we need a way to get their ID or rely on the token for user context
        pass


    login_data = {"username": username, "password": password}
    token_response = client.post(f"{settings.API_STR}/token", data=login_data)
    if token_response.status_code != 200:
        raise Exception(f"Failed to log in user {username} to get token. Status: {token_response.status_code}, Detail: {token_response.text}")
    
    token_data = token_response.json()
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    
    # To get user_id if not from creation (e.g. user existed)
    if user_id == -1:
        me_response = client.get(f"{settings.API_STR}/users/me", headers=headers)
        if me_response.status_code == 200:
            user_id = me_response.json()["id"]
        else:
            raise Exception("Could not retrieve user_id for existing user.")
            
    return headers, user_id


def test_create_car_success(client: TestClient, db_session: Session):
    auth_headers, user_id = create_user_and_get_headers(client, "creator", "pass")
    
    car_data = {
        "make": "Toyota",
        "model": "Supra",
        "year": 2020,
        "trim": "GR"
    }
    response = client.post(f"{settings.API_STR}/cars/", json=car_data, headers=auth_headers)
    assert response.status_code == 200, response.text
    created_car = response.json()
    assert created_car["make"] == car_data["make"]
    assert created_car["model"] == car_data["model"]
    assert created_car["year"] == car_data["year"]
    assert created_car["trim"] == car_data["trim"]
    assert "id" in created_car
    assert created_car["user_id"] == user_id

def test_create_car_unauthenticated(client: TestClient):
    car_data = {"make": "Honda", "model": "Civic", "year": 2021}
    response = client.post(f"{settings.API_STR}/cars/", json=car_data)
    assert response.status_code == 401 # Expecting 401 Unauthorized

def test_read_car_success(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "reader", "pass")
    car_data = {"make": "Mazda", "model": "MX-5", "year": 2019}
    create_response = client.post(f"{settings.API_STR}/cars/", json=car_data, headers=auth_headers)
    assert create_response.status_code == 200
    car_id = create_response.json()["id"]

    # As per current cars.py, read_car does not require authentication or check ownership
    response = client.get(f"{settings.API_STR}/cars/{car_id}")
    assert response.status_code == 200, response.text
    read_car_data = response.json()
    assert read_car_data["id"] == car_id
    assert read_car_data["make"] == car_data["make"]

def test_read_car_non_existent(client: TestClient):
    response = client.get(f"{settings.API_STR}/cars/999999") # Assuming this ID won't exist
    assert response.status_code == 404
    assert response.json()["detail"] == "Car not found"

def test_update_own_car_success(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "updater", "pass")
    car_data_initial = {"make": "Nissan", "model": "GT-R", "year": 2018, "trim": "Nismo"}
    create_response = client.post(f"{settings.API_STR}/cars/", json=car_data_initial, headers=auth_headers)
    assert create_response.status_code == 200
    car_id = create_response.json()["id"]

    update_payload = {"year": 2019, "trim": "Track Edition"}
    response = client.put(f"{settings.API_STR}/cars/{car_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 200, response.text
    updated_car = response.json()
    assert updated_car["year"] == 2019
    assert updated_car["trim"] == "Track Edition"
    assert updated_car["make"] == car_data_initial["make"] # Make should remain unchanged

def test_update_car_unauthenticated(client: TestClient, db_session: Session):
    # Setup: Create a car first by an authenticated user
    auth_headers, _ = create_user_and_get_headers(client, "owner_for_update_unauth", "pass")
    car_data = {"make": "Subaru", "model": "WRX", "year": 2020}
    create_response = client.post(f"{settings.API_STR}/cars/", json=car_data, headers=auth_headers)
    assert create_response.status_code == 200
    car_id = create_response.json()["id"]

    update_payload = {"year": 2021}
    response = client.put(f"{settings.API_STR}/cars/{car_id}", json=update_payload) # No auth headers
    assert response.status_code == 401

def test_update_other_users_car_forbidden(client: TestClient, db_session: Session):
    # User A creates a car
    auth_headers_a, _ = create_user_and_get_headers(client, "userA_car_owner", "passA")
    car_data_a = {"make": "Ford", "model": "Mustang", "year": 2020}
    create_response_a = client.post(f"{settings.API_STR}/cars/", json=car_data_a, headers=auth_headers_a)
    assert create_response_a.status_code == 200
    car_id_a = create_response_a.json()["id"]

    # User B tries to update User A's car
    auth_headers_b, _ = create_user_and_get_headers(client, "userB_attacker", "passB")
    update_payload = {"year": 2021}
    response = client.put(f"{settings.API_STR}/cars/{car_id_a}", json=update_payload, headers=auth_headers_b)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to update this car"

def test_delete_own_car_success(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "deleter", "pass")
    car_data = {"make": "BMW", "model": "M3", "year": 2021}
    create_response = client.post(f"{settings.API_STR}/cars/", json=car_data, headers=auth_headers)
    assert create_response.status_code == 200
    car_id = create_response.json()["id"]

    response = client.delete(f"{settings.API_STR}/cars/{car_id}", headers=auth_headers)
    assert response.status_code == 200, response.text
    deleted_car_data = response.json()
    assert deleted_car_data["id"] == car_id

    # Verify car is deleted
    get_response = client.get(f"{settings.API_STR}/cars/{car_id}") # No auth needed for GET as per current code
    assert get_response.status_code == 404

def test_delete_car_unauthenticated(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "owner_for_delete_unauth", "pass")
    car_data = {"make": "Audi", "model": "R8", "year": 2019}
    create_response = client.post(f"{settings.API_STR}/cars/", json=car_data, headers=auth_headers)
    assert create_response.status_code == 200
    car_id = create_response.json()["id"]

    response = client.delete(f"{settings.API_STR}/cars/{car_id}") # No auth headers
    assert response.status_code == 401

def test_delete_other_users_car_forbidden(client: TestClient, db_session: Session):
    auth_headers_a, _ = create_user_and_get_headers(client, "userA_car_owner_del", "passA")
    car_data_a = {"make": "Porsche", "model": "911", "year": 2022}
    create_response_a = client.post(f"{settings.API_STR}/cars/", json=car_data_a, headers=auth_headers_a)
    assert create_response_a.status_code == 200
    car_id_a = create_response_a.json()["id"]

    auth_headers_b, _ = create_user_and_get_headers(client, "userB_deleter_attacker", "passB")
    response = client.delete(f"{settings.API_STR}/cars/{car_id_a}", headers=auth_headers_b)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to delete this car"

def test_delete_car_not_found(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "deleter_notfound", "pass")
    response = client.delete(f"{settings.API_STR}/cars/888888", headers=auth_headers) # Non-existent ID
    assert response.status_code == 404
    assert response.json()["detail"] == "Car not found"
