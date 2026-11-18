from decimal import Decimal

def test_create_account(client, auth_headers):

    response = client.post(
        "/accounts/",
        json ={"currency": "GBP"},
        headers=auth_headers()
    )
    assert response.status_code == 201

    balance = response.json()["balance"]
    currency = response.json()["currency"]

    assert Decimal(str(balance)) == Decimal("0.00")
    assert currency == "GBP"

def test_create_account_without_token(client):

    response = client.post(
            "/accounts/",
            json ={"currency": "GBP"},
        )
    assert response.status_code == 401

def test_get_accounts(client, auth_headers):
    headers = auth_headers()

    response = client.post(
        "/accounts/",
        json = {"currency": "GBP"},
        headers=headers
    )

    assert response.status_code == 201

    account_id = response.json()["id"]

    account_response = client.get(
        "/accounts/",
        headers=headers
    )

    assert account_response.status_code == 200

    account_ids = [
        account["id"]
        for account in account_response.json()
    ]

    assert account_id in account_ids

def test_accounts_isolation(client, auth_headers):
    headers_a = auth_headers()
    headers_b = auth_headers()

    response_a = client.post(
        "/accounts/",
        json={"currency": "GBP"},
        headers=headers_a
    )
    assert response_a.status_code == 201
    account_a_id = response_a.json()["id"]

    response_b_post = client.post(
            "/accounts/",
            json={"currency": "GBP"},
            headers=headers_b
        )
    assert response_b_post.status_code == 201
    account_b_id = response_b_post.json()["id"]

    response_b = client.get(
        "/accounts/",
        headers=headers_b
    )

    assert response_b.status_code == 200

    account_b_ids =[
        account["id"]
        for account in response_b.json()
    ]

    assert account_a_id not in account_b_ids
    assert account_b_id in account_b_ids






































