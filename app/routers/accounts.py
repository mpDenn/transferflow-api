import secrets

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.account import Account
from app.models.user import User
from app.schemas.account import AccountCreate, AccountRead
from sqlalchemy import select

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
)

@router.post("/", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    account_data:AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):

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