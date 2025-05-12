from fastapi.testclient import TestClient

def test_read_root(client: TestClient): # Inject the client fixture
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

