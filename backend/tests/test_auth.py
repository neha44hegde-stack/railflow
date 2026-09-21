def test_register_and_login(client):
    r = client.post("/api/auth/register", json={
        "name": "Alice", "email": "alice@example.com", "password": "secret123"})
    assert r.status_code == 201
    r = client.post("/api/auth/login", json={"email": "alice@example.com", "password": "secret123"})
    assert r.status_code == 200
    assert "access_token" in r.get_json()


def test_duplicate_email(client):
    client.post("/api/auth/register", json={"name": "A", "email": "a@x.com", "password": "secret123"})
    r = client.post("/api/auth/register", json={"name": "A", "email": "a@x.com", "password": "secret123"})
    assert r.status_code == 409


def test_invalid_login(client):
    r = client.post("/api/auth/login", json={"email": "none@x.com", "password": "x"})
    assert r.status_code == 401
