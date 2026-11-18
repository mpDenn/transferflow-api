from decimal import Decimal
from app.models.account import Account
from sqlalchemy import event, select
from app.models.ledger_entry import LedgerEntry, EntryType
import pytest
from app.models.transfer import Transfer

def test_transfer_insufficient_funds(client, auth_headers):
    headhers = auth_headers()

    response1 = client.post(
        "/accounts/",
        json ={"currency": "GBP"},
        headers=headhers
    )
    assert response1.status_code == 201
    from_account_id = response1.json()["id"]

    response2 = client.post(
        "/accounts/",
        json ={"currency": "GBP"},
        headers=headhers
    )
    assert response2.status_code == 201
    to_account_number = response2.json()["account_number"]

    transfer_response = client.post(
        "/transfers/",
        json = {
            "from_account_id": from_account_id,
            "to_account_number": to_account_number,
            "amount": "25.00"
        },
        headers={**headhers, "idempotency-key": "insufficient-founds-001"},
    )

    assert transfer_response.status_code == 409
    assert transfer_response.json()["detail"] == "Insufficient funds"

    accounts_response = client.get(
        "/accounts/",
        headers=headhers
    )

    assert accounts_response.status_code == 200
    balances = {
        account["id"]: account["balance"]
        for account in accounts_response.json()
    }
    to_account_id = response2.json()["id"]

    assert Decimal(str(balances[from_account_id])) == Decimal("0.00")
    assert Decimal(str(balances[to_account_id])) == Decimal("0.00")

def test_transfer_success(client, auth_headers, db_session):
    headhers = auth_headers()

    response1 = client.post(
        "/accounts/",
        json ={"currency": "GBP"},
        headers=headhers
    )
    assert response1.status_code == 201
    from_account_id = response1.json()["id"]

    response2 = client.post(
        "/accounts/",
        json ={"currency": "GBP"},
        headers=headhers
    )
    assert response2.status_code == 201
    to_account_number = response2.json()["account_number"]

    sender = db_session.get(Account, from_account_id)
    sender.balance = Decimal("100.00")
    db_session.commit()

    transfer_response = client.post(
        "/transfers/",
        json = {
            "from_account_id": from_account_id,
            "to_account_number": to_account_number,
            "amount": "25.00"
        },
        headers={**headhers, "idempotency-key": "insufficient-success-001"},
    )

    assert transfer_response.status_code == 201

    accounts_response = client.get(
        "/accounts/",
        headers=headhers
    )

    assert accounts_response.status_code == 200
    balances = {
        account["id"]: account["balance"]
        for account in accounts_response.json()
    }
    to_account_id = response2.json()["id"]

    assert Decimal(str(balances[from_account_id])) == Decimal("75.00")
    assert Decimal(str(balances[to_account_id])) == Decimal("25.00")

    transfer_id = transfer_response.json()["id"]
    stmt = select(LedgerEntry).where(LedgerEntry.transfer_id == transfer_id)
    entries = db_session.execute(stmt).scalars().all()

    assert len(entries) == 2

    entries_by_type = {entry.entry_type: entry for entry in entries}
    debit = entries_by_type[EntryType.DEBIT]
    credit = entries_by_type[EntryType.CREDIT]

    assert debit.account_id == from_account_id
    assert credit.account_id == to_account_id
    assert debit.amount == Decimal("25.00")
    assert credit.amount == Decimal("25.00")

def test_transfer_idempotency(client, auth_headers, db_session):

    headhers = auth_headers()

    response1 = client.post(
        "/accounts/",
        json ={"currency": "GBP"},
        headers=headhers
    )
    assert response1.status_code == 201
    from_account_id = response1.json()["id"]

    response2 = client.post(
        "/accounts/",
        json ={"currency": "GBP"},
        headers=headhers
    )
    assert response2.status_code == 201
    to_account_number = response2.json()["account_number"]


    sender = db_session.get(Account, from_account_id)
    sender.balance = Decimal("100.00")
    db_session.commit()

    transfer_response = client.post(
        "/transfers/",
        json = {
            "from_account_id": from_account_id,
            "to_account_number": to_account_number,
            "amount": "25.00"
        },
        headers={**headhers, "idempotency-key": "insufficient-repeat-001"},
    )
    assert transfer_response.status_code == 201

    repeat_response = client.post(
        "/transfers/",
        json = {
            "from_account_id": from_account_id,
            "to_account_number": to_account_number,
            "amount": "25.00"
        },
        headers={**headhers, "idempotency-key": "insufficient-repeat-001"},
    )
    assert repeat_response.status_code == 201
    assert repeat_response.json()["id"] == transfer_response.json()["id"]

    accounts_response = client.get(
        "/accounts/",
        headers=headhers
    )

    assert accounts_response.status_code == 200
    balances = {
        account["id"]: account["balance"]
        for account in accounts_response.json()
    }
    to_account_id = response2.json()["id"]

    assert Decimal(str(balances[from_account_id])) == Decimal("75.00")
    assert Decimal(str(balances[to_account_id])) == Decimal("25.00")

    transfer_id = transfer_response.json()["id"]
    stmt = select(LedgerEntry).where(LedgerEntry.transfer_id == transfer_id)
    entries = db_session.execute(stmt).scalars().all()

    assert len(entries) == 2

def test_transfer_idempotency_conflict(client, auth_headers, db_session):

    headhers = auth_headers()

    response1 = client.post(
        "/accounts/",
        json ={"currency": "GBP"},
        headers=headhers
    )
    assert response1.status_code == 201
    from_account_id = response1.json()["id"]

    response2 = client.post(
        "/accounts/",
        json ={"currency": "GBP"},
        headers=headhers
    )
    assert response2.status_code == 201
    to_account_number = response2.json()["account_number"]

    sender = db_session.get(Account, from_account_id)
    sender.balance = Decimal("100.00")
    db_session.commit()

    transfer_response = client.post(
        "/transfers/",
        json = {
            "from_account_id": from_account_id,
            "to_account_number": to_account_number,
            "amount": "25.00"
        },
        headers={**headhers, "idempotency-key": "insufficient-conflict-001"},
    )
    assert transfer_response.status_code == 201

    repeat_response = client.post(
        "/transfers/",
        json = {
            "from_account_id": from_account_id,
            "to_account_number": to_account_number,
            "amount": "30.00"
        },
        headers={**headhers, "idempotency-key": "insufficient-conflict-001"},
    )
    assert repeat_response.status_code == 409
    assert repeat_response.json()["detail"] == "Idempotency key was already used for another transfer"

def test_transfer_rolls_back_on_ledger_error(client, auth_headers, db_session):
    headhers = auth_headers()

    response1 = client.post(
        "/accounts/",
        json ={"currency": "GBP"},
        headers=headhers
    )
    assert response1.status_code == 201
    from_account_id = response1.json()["id"]

    response2 = client.post(
        "/accounts/",
        json ={"currency": "GBP"},
        headers=headhers
    )
    assert response2.status_code == 201
    to_account_number = response2.json()["account_number"]

    sender = db_session.get(Account, from_account_id)
    sender.balance = Decimal("100.00")
    db_session.commit()

    def fail_on_credit(_mapper, _connection, entry):
        if entry.entry_type == EntryType.CREDIT:
            raise RuntimeError("Test credit insert failed")

    event.listen(LedgerEntry, "before_insert", fail_on_credit)
    try:
        with pytest.raises(RuntimeError, match="Test credit insert failed"):
            transfer_response = client.post(
                "/transfers/",
                    json = {
                    "from_account_id": from_account_id,
                    "to_account_number": to_account_number,
                    "amount": "25.00"
                },
                headers={**headhers, "idempotency-key": "transfer-rollback-001"},
            )
    finally:
        event.remove(LedgerEntry, "before_insert", fail_on_credit)

    accounts_response = client.get(
        "/accounts/",
        headers=headhers
    )

    assert accounts_response.status_code == 200
    balances = {
        account["id"]: account["balance"]
        for account in accounts_response.json()
    }
    to_account_id = response2.json()["id"]

    assert Decimal(str(balances[from_account_id])) == Decimal("100.00")
    assert Decimal(str(balances[to_account_id])) == Decimal("0.00")

    stmt = select(Transfer).where(Transfer.idempotency_key == "transfer-rollback-001")
    transfer = db_session.execute(stmt).scalar_one_or_none()

    assert transfer is None

    stmt = select(LedgerEntry).where(
        LedgerEntry.account_id.in_([from_account_id, to_account_id])
    )
    entries = db_session.execute(stmt).scalars().all()
    assert entries == []











