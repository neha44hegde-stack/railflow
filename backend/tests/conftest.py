import pytest
from app import create_app
from extensions import db as _db
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-secret"


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth(client):
    def register_and_login(email, password="secret123", role="PASSENGER"):
        client.post("/api/auth/register", json={
            "name": "Test", "email": email, "password": password, "role": role,
        })
        r = client.post("/api/auth/login", json={"email": email, "password": password})
        token = r.get_json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return register_and_login
