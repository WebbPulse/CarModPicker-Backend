from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.api.schemas.part import PartRead, PartCreate, PartUpdate
from app.core.config import settings

# Helper functions adapted from test_build_lists.py
def create_user_and_get_headers(client: TestClient, username_suffix: str) -> tuple[dict, int]:
    username = f"part_test_user_{username_suffix}"
    email = f"part_test_user_{username_suffix}@example.com"
    password = "testpassword"
    
    user_data = {
        "username": username,
        "email": email,
        "password": password,
        "first_name": "PartTest",
        "last_name": username_suffix.capitalize()
    }
    response = client.post(f"{settings.API_STR}/users/", json=user_data)
    user_id = -1
    if response.status_code == 200:
        user_id = response.json()["id"]
    elif response.status_code == 400 and "already registered" in response.json().get("detail", ""):
        pass # User might exist
    else:
        raise Exception(f"Failed to create user {username}. Status: {response.status_code}, Detail: {response.text}")

    login_data = {"username": username, "password": password}
    token_response = client.post(f"{settings.API_STR}/token", data=login_data)
    if token_response.status_code != 200:
        raise Exception(f"Failed to log in user {username}. Status: {token_response.status_code}, Detail: {token_response.text}")
    
    token_data = token_response.json()
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    
    if user_id == -1: # If user existed, get ID
        me_response = client.get(f"{settings.API_STR}/users/me", headers=headers)
        if me_response.status_code == 200:
            user_id = me_response.json()["id"]
        else:
            raise Exception(f"Could not retrieve user_id for existing user {username}. Status: {me_response.status_code}, Detail: {me_response.text}")
            
    return headers, user_id

def create_car_for_user(client: TestClient, headers: dict, car_make: str = "TestMakePart", car_model: str = "TestModelPart") -> int:
    car_data = {"make": car_make, "model": car_model, "year": 2023, "trim": "TestTrimPart"}
    response = client.post(f"{settings.API_STR}/cars/", json=car_data, headers=headers)
    assert response.status_code == 200, f"Failed to create car: {response.text}"
    return response.json()["id"]

def create_build_list_for_car(client: TestClient, headers: dict, car_id: int, bl_name: str = "Test Build List for Part") -> int:
    build_list_data = {"name": bl_name, "description": "A list for testing parts", "car_id": car_id}
    response = client.post(f"{settings.API_STR}/build_lists/", json=build_list_data, headers=headers)
    assert response.status_code == 200, f"Failed to create build list: {response.text}"
    return response.json()["id"]

# Tests for Parts Endpoints

def test_create_part_success(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "part_creator")
    car_id = create_car_for_user(client, auth_headers)
    build_list_id = create_build_list_for_car(client, auth_headers, car_id)
    
    part_data = {
        "name": "Performance Exhaust",
        "part_type": "Exhaust",
        "manufacturer": "BrandX",
        "price": 500,
        "build_list_id": build_list_id
    }
    response = client.post(f"{settings.API_STR}/parts/", json=part_data, headers=auth_headers)
    assert response.status_code == 200, response.text
    created_part = response.json()
    assert created_part["name"] == part_data["name"]
    assert created_part["build_list_id"] == build_list_id
    assert "id" in created_part

def test_create_part_unauthenticated(client: TestClient, db_session: Session):
    auth_headers_temp, _ = create_user_and_get_headers(client, "part_temp_owner")
    car_id_temp = create_car_for_user(client, auth_headers_temp)
    build_list_id_temp = create_build_list_for_car(client, auth_headers_temp, car_id_temp)

    part_data = {"name": "Unauthorized Part", "build_list_id": build_list_id_temp}
    response = client.post(f"{settings.API_STR}/parts/", json=part_data) # No auth_headers
    assert response.status_code == 401

def test_create_part_for_other_users_build_list_forbidden(client: TestClient, db_session: Session):
    # User A creates a build list
    auth_headers_a, _ = create_user_and_get_headers(client, "userA_part_bl_owner")
    car_id_a = create_car_for_user(client, auth_headers_a)
    build_list_id_a = create_build_list_for_car(client, auth_headers_a, car_id_a)

    # User B tries to create a part for User A's build list
    auth_headers_b, _ = create_user_and_get_headers(client, "userB_part_attacker")
    part_data = {"name": "Attacker's Part", "build_list_id": build_list_id_a}
    response = client.post(f"{settings.API_STR}/parts/", json=part_data, headers=auth_headers_b)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to add a part to this build list"

def test_create_part_build_list_not_found(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "part_bl_not_found")
    non_existent_bl_id = 999888
    part_data = {"name": "Part for Non-existent BL", "build_list_id": non_existent_bl_id}
    response = client.post(f"{settings.API_STR}/parts/", json=part_data, headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Build List not found" # Matches _verify_build_list_ownership

def test_read_part_success(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "part_reader")
    car_id = create_car_for_user(client, auth_headers)
    build_list_id = create_build_list_for_car(client, auth_headers, car_id)
    part_data = {"name": "Readable Part", "build_list_id": build_list_id}
    create_response = client.post(f"{settings.API_STR}/parts/", json=part_data, headers=auth_headers)
    assert create_response.status_code == 200
    part_id = create_response.json()["id"]

    response = client.get(f"{settings.API_STR}/parts/{part_id}") # No auth needed for read as per current endpoint
    assert response.status_code == 200, response.text
    read_part_data = response.json()
    assert read_part_data["id"] == part_id
    assert read_part_data["name"] == part_data["name"]

def test_read_part_not_found(client: TestClient, db_session: Session):
    response = client.get(f"{settings.API_STR}/parts/777666") # Assuming this ID won't exist
    assert response.status_code == 404
    assert response.json()["detail"] == "part not found" # Matches endpoint message

def test_update_own_part_success(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "part_updater")
    car_id = create_car_for_user(client, auth_headers)
    build_list_id = create_build_list_for_car(client, auth_headers, car_id)
    part_data_initial = {"name": "Initial Part Name", "manufacturer": "OldBrand", "build_list_id": build_list_id}
    create_response = client.post(f"{settings.API_STR}/parts/", json=part_data_initial, headers=auth_headers)
    assert create_response.status_code == 200
    part_id = create_response.json()["id"]

    update_payload = {"name": "Updated Part Name", "manufacturer": "NewBrand"}
    response = client.put(f"{settings.API_STR}/parts/{part_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 200, response.text
    updated_part = response.json()
    assert updated_part["name"] == update_payload["name"]
    assert updated_part["manufacturer"] == update_payload["manufacturer"]
    assert updated_part["build_list_id"] == build_list_id # BL ID should remain unchanged

def test_update_own_part_change_build_list_success(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "part_bl_changer")
    car_id = create_car_for_user(client, auth_headers)
    build_list_id_1 = create_build_list_for_car(client, auth_headers, car_id, "BL1 for Part")
    build_list_id_2 = create_build_list_for_car(client, auth_headers, car_id, "BL2 for Part") # User owns both BLs

    part_data_initial = {"name": "Part to Move", "build_list_id": build_list_id_1}
    create_response = client.post(f"{settings.API_STR}/parts/", json=part_data_initial, headers=auth_headers)
    assert create_response.status_code == 200
    part_id = create_response.json()["id"]

    update_payload = {"build_list_id": build_list_id_2}
    response = client.put(f"{settings.API_STR}/parts/{part_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 200, response.text
    updated_part = response.json()
    assert updated_part["build_list_id"] == build_list_id_2
    assert updated_part["name"] == part_data_initial["name"]

def test_update_part_unauthenticated(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "owner_for_part_update_unauth")
    car_id = create_car_for_user(client, auth_headers)
    bl_id = create_build_list_for_car(client, auth_headers, car_id)
    part_data = {"name": "Some Part", "build_list_id": bl_id}
    create_response = client.post(f"{settings.API_STR}/parts/", json=part_data, headers=auth_headers)
    assert create_response.status_code == 200
    part_id = create_response.json()["id"]

    update_payload = {"name": "New Part Name Unauth"}
    response = client.put(f"{settings.API_STR}/parts/{part_id}", json=update_payload) # No auth headers
    assert response.status_code == 401

def test_update_part_not_found(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "updater_part_notfound")
    update_payload = {"name": "Update Non Existent Part"}
    response = client.put(f"{settings.API_STR}/parts/555444", json=update_payload, headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "part not found"

def test_update_other_users_part_forbidden(client: TestClient, db_session: Session):
    # User A creates a part
    auth_headers_a, _ = create_user_and_get_headers(client, "userA_part_owner")
    car_id_a = create_car_for_user(client, auth_headers_a)
    bl_id_a = create_build_list_for_car(client, auth_headers_a, car_id_a)
    part_data_a = {"name": "User A's Part", "build_list_id": bl_id_a}
    create_response_a = client.post(f"{settings.API_STR}/parts/", json=part_data_a, headers=auth_headers_a)
    assert create_response_a.status_code == 200
    part_id_a = create_response_a.json()["id"]

    # User B tries to update User A's part
    auth_headers_b, _ = create_user_and_get_headers(client, "userB_part_updater_attacker")
    update_payload = {"name": "Malicious Part Update"}
    response = client.put(f"{settings.API_STR}/parts/{part_id_a}", json=update_payload, headers=auth_headers_b)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to update this part"

def test_update_part_to_other_users_build_list_forbidden(client: TestClient, db_session: Session):
    # User A creates their own part on their own build list
    auth_headers_a, _ = create_user_and_get_headers(client, "userA_part_bl_switcher")
    car_id_a = create_car_for_user(client, auth_headers_a)
    bl_id_a_own = create_build_list_for_car(client, auth_headers_a, car_id_a, "User A BL Own")
    part_data_a = {"name": "User A's Part to Move", "build_list_id": bl_id_a_own}
    create_response_a = client.post(f"{settings.API_STR}/parts/", json=part_data_a, headers=auth_headers_a)
    assert create_response_a.status_code == 200
    part_id_a = create_response_a.json()["id"]

    # User B creates a build list
    auth_headers_b, _ = create_user_and_get_headers(client, "userB_bl_owner_target_part")
    car_id_b = create_car_for_user(client, auth_headers_b)
    bl_id_b_target = create_build_list_for_car(client, auth_headers_b, car_id_b, "User B BL Target")

    # User A tries to update their part to point to User B's build list
    update_payload = {"build_list_id": bl_id_b_target}
    response = client.put(f"{settings.API_STR}/parts/{part_id_a}", json=update_payload, headers=auth_headers_a)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to move part to the new build list"

def test_update_part_to_non_existent_build_list_not_found(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "part_to_non_bl_updater")
    car_id = create_car_for_user(client, auth_headers)
    bl_id_own = create_build_list_for_car(client, auth_headers, car_id)
    part_data = {"name": "Part for BL Update Test", "build_list_id": bl_id_own}
    create_response = client.post(f"{settings.API_STR}/parts/", json=part_data, headers=auth_headers)
    assert create_response.status_code == 200
    part_id = create_response.json()["id"]

    non_existent_bl_id = 999777
    update_payload = {"build_list_id": non_existent_bl_id}
    response = client.put(f"{settings.API_STR}/parts/{part_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == f"New Build List with id {non_existent_bl_id} not found"

def test_delete_own_part_success(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "part_deleter")
    car_id = create_car_for_user(client, auth_headers)
    bl_id = create_build_list_for_car(client, auth_headers, car_id)
    part_data = {"name": "Part to Delete", "build_list_id": bl_id}
    create_response = client.post(f"{settings.API_STR}/parts/", json=part_data, headers=auth_headers)
    assert create_response.status_code == 200
    part_id = create_response.json()["id"]

    response = client.delete(f"{settings.API_STR}/parts/{part_id}", headers=auth_headers)
    assert response.status_code == 200, response.text
    deleted_part_data = response.json()
    assert deleted_part_data["id"] == part_id

    # Verify part is deleted
    get_response = client.get(f"{settings.API_STR}/parts/{part_id}")
    assert get_response.status_code == 404

def test_delete_part_unauthenticated(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "owner_for_part_delete_unauth")
    car_id = create_car_for_user(client, auth_headers)
    bl_id = create_build_list_for_car(client, auth_headers, car_id)
    part_data = {"name": "Part to be deleted unauth", "build_list_id": bl_id}
    create_response = client.post(f"{settings.API_STR}/parts/", json=part_data, headers=auth_headers)
    assert create_response.status_code == 200
    part_id = create_response.json()["id"]

    response = client.delete(f"{settings.API_STR}/parts/{part_id}") # No auth headers
    assert response.status_code == 401

def test_delete_part_not_found(client: TestClient, db_session: Session):
    auth_headers, _ = create_user_and_get_headers(client, "deleter_part_notfound")
    response = client.delete(f"{settings.API_STR}/parts/333222", headers=auth_headers) # Non-existent ID
    assert response.status_code == 404
    assert response.json()["detail"] == "part not found"

def test_delete_other_users_part_forbidden(client: TestClient, db_session: Session):
    # User A creates a part
    auth_headers_a, _ = create_user_and_get_headers(client, "userA_part_owner_del")
    car_id_a = create_car_for_user(client, auth_headers_a)
    bl_id_a = create_build_list_for_car(client, auth_headers_a, car_id_a)
    part_data_a = {"name": "User A's Part for Deletion Test", "build_list_id": bl_id_a}
    create_response_a = client.post(f"{settings.API_STR}/parts/", json=part_data_a, headers=auth_headers_a)
    assert create_response_a.status_code == 200
    part_id_a = create_response_a.json()["id"]

    # User B tries to delete User A's part
    auth_headers_b, _ = create_user_and_get_headers(client, "userB_part_deleter_attacker")
    response = client.delete(f"{settings.API_STR}/parts/{part_id_a}", headers=auth_headers_b)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to delete this part"