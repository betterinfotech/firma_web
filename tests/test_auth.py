import pytest
from app import create_app
import jwt
from app.config import SECRET_KEY


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json == {"message": "Auth server is running."}


def test_get_token_success(client):
    response = client.post(
        "/get-token", json={"device_id": "LAPTOP-S2QSIFSL", "auth_user": "Lenovo"}
    )
    assert response.status_code == 200
    assert "token" in response.json


def test_get_token_missing_data(client):
    response = client.post("/get-token", json={})
    assert response.status_code == 400
    assert "error" in response.json


def test_get_token_invalid_user(client):
    response = client.post(
        "/get-token", json={"device_id": "FAKE_DEVICE", "auth_user": "WrongUser"}
    )
    assert response.status_code == 401
    assert "error" in response.json


def test_verify_token_success(client):
    # Generate a token first
    payload = {"device_id": "LAPTOP-S2QSIFSL", "auth_user": "Lenovo"}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    response = client.post(
        "/verify-token", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json.get("valid") is True


def test_verify_token_missing(client):
    response = client.post("/verify-token", headers={})
    assert response.status_code == 401


def test_secure_data_success(client):
    payload = {"device_id": "LAPTOP-S2QSIFSL", "auth_user": "Lenovo"}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    response = client.get("/secure-data", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "message" in response.json


def test_secure_data_invalid_token(client):
    response = client.get(
        "/secure-data", headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert response.status_code == 401
    assert "error" in response.json
