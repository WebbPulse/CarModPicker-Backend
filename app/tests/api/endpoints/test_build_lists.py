from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.api.schemas.build_list import BuildListRead, BuildListCreate, BuildListUpdate
from app.core.config import settings

# Helper function to create a user and get auth headers
# Adapted from your existing test files
def create_user_and_get_headers(client: TestClient, username_suffix: str) -> tuple[dict, int]:
    username = f"bl_test_user_{username_suffix}"
    email = f"bl_test_user_{username_suffix}@example.com"
    password = "testpassword"
    
    user_data = {
        "username": username,
        "email": email,
        "password": password,
        "first_name": "BLTest",
        "last_name": username_suffix.capitalize()
    }
    # Create user
    response = client.post(f"{settings.API_STR}/users/", json=user_data)
    user_id = -1
    if response.status_code == 200:
        user_id = response.json()["id"]
    elif response.status_code == 400 and "already registered" in response.json().get("detail", ""):
        # User might exist from a previous run, try to log in to get ID
        pass
    else:
        raise Exception(f"Failed to create user {username} for build list tests. Status: {response.status_code}, Detail: {response.text}")

    # Log in to get token
    login_data = {"username": username, "password": password}
    token_response = client.post(f"{settings.API_STR}/token", data=login_data)
    if token_response.status_code != 200:
        raise Exception(f"Failed to log in user {username} to get token. Status: {token_response.status_code}, Detail: {token_response.text}")
    
    token_data = token_response.json()
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    
    # If user_id was not set during creation (because user existed), get it now
    if user_id == -1:
        me_response = client.get(f"{settings.API_STR}/users/me", headers=headers)
        if me_response.status_code == 200:
            user_id = me_response.json()["id"]
        else:
            raise Exception(f"Could not retrieve user_id for existing user {username}. Status: {me_response.status_code}, Detail: {me_response.text}")
            
    return headers, user_id

# Helper function to create a car for a user
def create_car_for_user(client: TestClient, headers: dict, car_make: str = "TestMake", car_model: str = "TestModel") -> int:
    car_data = {
        "make": car_make,
        "model": car_model,
        "year": 2023,
        "trim": "TestTrim"
    }
    response = client.post(f"{settings.API_STR}/cars/", json=car_data, headers=headers)
    assert response.status_code == 200, f"Failed to create car: {response.text}"
    return response.json()["id"]


def test_create_build_list_success(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "creator_bl")
    car_id = create_car_for_user(client, auth_headers, "Toyota", "Supra")
    
    build_list_data = {
        "name": "My Supra Build",
        "description": "Performance upgrades for track days",
        "car_id": car_id
    }
    response = client.post(f"{settings.API_STR}/build_lists/", json=build_list_data, headers=auth_headers)
    assert response.status_code == 200, response.text
    created_bl = response.json()
    assert created_bl["name"] == build_list_data["name"]
    assert created_bl["description"] == build_list_data["description"]
    assert created_bl["car_id"] == car_id
    assert "id" in created_bl

def test_create_build_list_unauthenticated(client: TestClient, db_session: Session):
    # Need a car_id, but it doesn't matter who owns it for this test, as auth fails first
    # However, to get a car_id, we need a user and car first.
    auth_headers_temp, _ = create_user_and_get_headers(client, "temp_owner_bl")
    car_id_temp = create_car_for_user(client, auth_headers_temp)

    build_list_data = {"name": "Unauthorized Build", "car_id": car_id_temp}
    response = client.post(f"{settings.API_STR}/build_lists/", json=build_list_data) # No auth_headers
    assert response.status_code == 401 # Expecting 401 Unauthorized

def test_create_build_list_car_not_found(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "car_not_found_bl")
    non_existent_car_id = 999999
    build_list_data = {
        "name": "Build for Non-existent Car",
        "car_id": non_existent_car_id
    }
    response = client.post(f"{settings.API_STR}/build_lists/", json=build_list_data, headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Car not found"

def test_create_build_list_for_other_users_car(client: TestClient, db_session: Session):
    # User A creates a car
    auth_headers_a, _ = create_user_and_get_headers(client, "userA_car_owner_bl")
    car_id_a = create_car_for_user(client, auth_headers_a, "Honda", "Civic")

    # User B tries to create a build list for User A's car
    auth_headers_b, _ = create_user_and_get_headers(client, "userB_bl_attacker")
    build_list_data = {
        "name": "Attacker's Build on User A's Car",
        "car_id": car_id_a
    }
    response = client.post(f"{settings.API_STR}/build_lists/", json=build_list_data, headers=auth_headers_b)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to create a build list for this car"

def test_read_build_list_success(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "reader_bl")
    car_id = create_car_for_user(client, auth_headers, "Mazda", "MX-5")
    build_list_data = {"name": "MX-5 Fun Build", "car_id": car_id}
    create_response = client.post(f"{settings.API_STR}/build_lists/", json=build_list_data, headers=auth_headers)
    assert create_response.status_code == 200
    build_list_id = create_response.json()["id"]

    response = client.get(f"{settings.API_STR}/build_lists/{build_list_id}") # No auth needed as per current endpoint
    assert response.status_code == 200, response.text
    read_bl_data = response.json()
    assert read_bl_data["id"] == build_list_id
    assert read_bl_data["name"] == build_list_data["name"]
    assert read_bl_data["car_id"] == car_id

def test_read_build_list_not_found(client: TestClient, db_session: Session):
    response = client.get(f"{settings.API_STR}/build_lists/999999") # Assuming this ID won't exist
    assert response.status_code == 404
    assert response.json()["detail"] == "Build List not found"

def test_update_own_build_list_success(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "updater_bl")
    car_id = create_car_for_user(client, auth_headers, "Nissan", "GT-R")
    build_list_data_initial = {"name": "Initial GT-R Build", "car_id": car_id}
    create_response = client.post(f"{settings.API_STR}/build_lists/", json=build_list_data_initial, headers=auth_headers)
    assert create_response.status_code == 200
    build_list_id = create_response.json()["id"]

    update_payload = {"name": "Updated GT-R Build", "description": "Now with more power!"}
    response = client.put(f"{settings.API_STR}/build_lists/{build_list_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 200, response.text
    updated_bl = response.json()
    assert updated_bl["name"] == update_payload["name"]
    assert updated_bl["description"] == update_payload["description"]
    assert updated_bl["car_id"] == car_id # Car ID should remain unchanged

def test_update_own_build_list_change_car_success(client: TestClient, db_session: Session):
    auth_headers, user_id = create_user_and_get_headers(client, "car_changer_bl")
    car_id_1 = create_car_for_user(client, auth_headers, "Subaru", "WRX")
    car_id_2 = create_car_for_user(client, auth_headers, "Mitsubishi", "Evo") # User owns both cars

    build_list_data_initial = {"name": "WRX Project", "car_id": car_id_1}
    create_response = client.post(f"{settings.API_STR}/build_lists/", json=build_list_data_initial, headers=auth_headers)
    assert create_response.status_code == 200
    build_list_id = create_response.json()["id"]

    update_payload = {"car_id": car_id_2}
    response = client.put(f"{settings.API_STR}/build_lists/{build_list_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 200, response.text
    updated_bl = response.json()
    assert updated_bl["car_id"] == car_id_2
    assert updated_bl["name"] == build_list_data_initial["name"]

def test_update_build_list_unauthenticated(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "owner_for_update_unauth_bl")
    car_id = create_car_for_user(client, auth_headers)
    bl_data = {"name": "Some Build", "car_id": car_id}
    create_response = client.post(f"{settings.API_STR}/build_lists/", json=bl_data, headers=auth_headers)
    assert create_response.status_code == 200
    bl_id = create_response.json()["id"]

    update_payload = {"name": "New Name Unauth"}
    response = client.put(f"{settings.API_STR}/build_lists/{bl_id}", json=update_payload) # No auth headers
    assert response.status_code == 401

def test_update_build_list_not_found(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "updater_bl_notfound")
    update_payload = {"name": "Update Non Existent"}
    response = client.put(f"{settings.API_STR}/build_lists/777777", json=update_payload, headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Build List not found"

def test_update_other_users_build_list_forbidden(client: TestClient, db_session: Session):
    # User A creates a car and a build list
    auth_headers_a, _ = create_user_and_get_headers(client, "userA_bl_owner")
    car_id_a = create_car_for_user(client, auth_headers_a, "Ford", "Mustang")
    bl_data_a = {"name": "User A's Build", "car_id": car_id_a}
    create_response_a = client.post(f"{settings.API_STR}/build_lists/", json=bl_data_a, headers=auth_headers_a)
    assert create_response_a.status_code == 200
    bl_id_a = create_response_a.json()["id"]

    # User B tries to update User A's build list
    auth_headers_b, _ = create_user_and_get_headers(client, "userB_bl_updater_attacker")
    update_payload = {"name": "Malicious Update"}
    response = client.put(f"{settings.API_STR}/build_lists/{bl_id_a}", json=update_payload, headers=auth_headers_b)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to update this build list"

def test_update_build_list_to_other_users_car_forbidden(client: TestClient, db_session: Session):
    # User A creates their own car and build list
    auth_headers_a, _ = create_user_and_get_headers(client, "userA_bl_car_switcher")
    car_id_a_own = create_car_for_user(client, auth_headers_a, "BMW", "M3")
    bl_data_a = {"name": "User A's M3 Build", "car_id": car_id_a_own}
    create_response_a = client.post(f"{settings.API_STR}/build_lists/", json=bl_data_a, headers=auth_headers_a)
    assert create_response_a.status_code == 200
    bl_id_a = create_response_a.json()["id"]

    # User B creates a car
    auth_headers_b, _ = create_user_and_get_headers(client, "userB_car_owner_target")
    car_id_b_target = create_car_for_user(client, auth_headers_b, "Audi", "R8")

    # User A tries to update their build list to point to User B's car
    update_payload = {"car_id": car_id_b_target}
    response = client.put(f"{settings.API_STR}/build_lists/{bl_id_a}", json=update_payload, headers=auth_headers_a)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to associate build list with the new car"

def test_update_build_list_to_non_existent_car_not_found(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "bl_to_non_car_updater")
    car_id_own = create_car_for_user(client, auth_headers, "Porsche", "911")
    bl_data = {"name": "911 Build", "car_id": car_id_own}
    create_response = client.post(f"{settings.API_STR}/build_lists/", json=bl_data, headers=auth_headers)
    assert create_response.status_code == 200
    bl_id = create_response.json()["id"]

    non_existent_car_id = 999888
    update_payload = {"car_id": non_existent_car_id}
    response = client.put(f"{settings.API_STR}/build_lists/{bl_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == f"New car with id {non_existent_car_id} not found"

def test_delete_own_build_list_success(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "deleter_bl")
    car_id = create_car_for_user(client, auth_headers, "Lexus", "LC500")
    bl_data = {"name": "LC500 Project", "car_id": car_id}
    create_response = client.post(f"{settings.API_STR}/build_lists/", json=bl_data, headers=auth_headers)
    assert create_response.status_code == 200
    bl_id = create_response.json()["id"]

    response = client.delete(f"{settings.API_STR}/build_lists/{bl_id}", headers=auth_headers)
    assert response.status_code == 200, response.text
    deleted_bl_data = response.json()
    assert deleted_bl_data["id"] == bl_id

    # Verify build list is deleted
    get_response = client.get(f"{settings.API_STR}/build_lists/{bl_id}")
    assert get_response.status_code == 404

def test_delete_build_list_unauthenticated(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "owner_for_delete_unauth_bl")
    car_id = create_car_for_user(client, auth_headers)
    bl_data = {"name": "Build to be deleted unauth", "car_id": car_id}
    create_response = client.post(f"{settings.API_STR}/build_lists/", json=bl_data, headers=auth_headers)
    assert create_response.status_code == 200
    bl_id = create_response.json()["id"]

    response = client.delete(f"{settings.API_STR}/build_lists/{bl_id}") # No auth headers
    assert response.status_code == 401

def test_delete_build_list_not_found(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "deleter_bl_notfound")
    response = client.delete(f"{settings.API_STR}/build_lists/666666", headers=auth_headers) # Non-existent ID
    assert response.status_code == 404
    assert response.json()["detail"] == "Build List not found"

def test_delete_other_users_build_list_forbidden(client: TestClient, db_session: Session):
    # User A creates a car and a build list
    auth_headers_a, _ = create_user_and_get_headers(client, "userA_bl_owner_del")
    car_id_a = create_car_for_user(client, auth_headers_a, "Ferrari", "488")
    bl_data_a = {"name": "User A's Ferrari Build", "car_id": car_id_a}
    create_response_a = client.post(f"{settings.API_STR}/build_lists/", json=bl_data_a, headers=auth_headers_a)
    assert create_response_a.status_code == 200
    bl_id_a = create_response_a.json()["id"]

    # User B tries to delete User A's build list
    auth_headers_b, _ = create_user_and_get_headers(client, "userB_bl_deleter_attacker")
    response = client.delete(f"{settings.API_STR}/build_lists/{bl_id_a}", headers=auth_headers_b)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to delete this build list"
