
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.account import AccountCreate, AccountRead

from app.services.account_service import create_account, get_accounts

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
)

@router.post("/", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account_endpoint(
    account_data:AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):

    return create_account(account_data, db, current_user)

@router.get("/", response_model=list[AccountRead])
def get_accounts_endpint(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
        ):

    return get_accounts(db, current_user)