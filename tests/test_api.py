
def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200

def test_register_user(client):
    response = client.post(
        "/users/",
        json = {
            "full_name": "Test User",
            "email": "test_register@example.com",
            "password": "Testpassword123!"
        }
    )

    assert response.status_code == 201
    assert response.json()["email"] == "test_register@example.com"

def test_login_user(client, user_factory):

    user = user_factory()

    response = client.post(
        "/auth/login",
        json={
            "email": user["email"],
            "password": user["password"]
        }
    )

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["access_token"]

def test_get_current_user(client, user_factory):
    user = user_factory()

    response = client.post(
        "/auth/login",
        json={
            "email": user["email"],
            "password": user["password"]
        }
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    me_response = client.get(
        "/users/me",
        headers={
            "Authorization": f"bearer {token}"
        }
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == user["email"]

def test_login_wrong_password(client, user_factory):
    user = user_factory()

    response = client.post(
        "/auth/login",
        json={
            "email": user["email"],
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401

def test_get_current_user_without_token(client):

    response = client.get(
        "/users/me"
    )

    assert response.status_code == 401

def test_auth_header(client, auth_headers):

    response = client.get(
        "/users/me",
        headers=auth_headers()
    )

    assert response.status_code == 200








