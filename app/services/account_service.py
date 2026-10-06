import secrets
from app.models.account import Account
from sqlalchemy import select

def create_account(account_data, db, current_user):
    while True:
        account_number = f"{secrets.randbelow(10**12):012d}"

        existing_number = db.execute(
            select(Account).where(Account.account_number == account_number)
            ).scalars().first()

        if not existing_number:
            break

    accunt = Account(
        user_id=current_user.id,
        account_number=account_number,
        currency=account_data.currency.upper()
    )

    db.add(accunt)
    db.commit()
    db.refresh(accunt)

    return accunt

def get_accounts(db, current_user):

    user_accounts = db.execute(
        select(Account).where(Account.user_id == current_user.id)
        ).scalars().all()

    return user_accounts