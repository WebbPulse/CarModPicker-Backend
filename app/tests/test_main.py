from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

# You will add more tests for authentication and CRUD endpoints here.
# For example, a test for user creation might look like this:

# def test_create_user():
#     response = client.post(
#         "/users/",
#         json={"username": "testuser", "email": "testuser@example.com", "password": "testpassword"},
#     )
#     assert response.status_code == 200 # or 201 if you change it
#     data = response.json()
#     assert data["email"] == "testuser@example.com"
#     assert "id" in data
#     # You would typically not return the password, even hashed, in a read operation.
#     # assert "hashed_password" not in data # Ensure password is not returned

# Remember to set up a test database and handle database sessions appropriately for integration tests.