import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Base, engine

client = TestClient(app)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    yield db
    Base.metadata.drop_all(bind=engine)


def test_register_user(db_session):
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "testpass123",
        "university": "Test University",
        "consent_given": True
    })
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


def test_register_without_consent(db_session):
    response = client.post("/api/auth/register", json={
        "email": "test2@example.com",
        "password": "testpass123",
        "consent_given": False
    })
    assert response.status_code == 400


def test_login(db_session):
    # Register first
    client.post("/api/auth/register", json={
        "email": "login@example.com",
        "password": "testpass123",
        "consent_given": True
    })
    
    # Login
    response = client.post("/api/auth/login", data={
        "username": "login@example.com",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

