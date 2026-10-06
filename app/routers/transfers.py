from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.transfer import TransferCreate, TransferRead
from app.services.transfer_service import create_transfer

router = APIRouter(
    prefix="/transfers",
    tags=["transfers"],
)

TRANSFER_ERROR_RESPONSES ={
        "FROM_ACCOUNT_NOT_FOUND":(
            status.HTTP_404_NOT_FOUND,
            "Source account not found",
        ),
        "TO_ACCOUNT_NOT_FOUND":(
            status.HTTP_404_NOT_FOUND,
             "Destination account not found",
        ),
        "SAME_ACCOUNT":(
            status.HTTP_400_BAD_REQUEST,
             "Cannot transfer to the same account",
        ),
        "ACCOUNT_INACTIVE":(
            status.HTTP_409_CONFLICT,
            "One of the accounts is inactive"
        ),
        "CURRENCY_MISMATCH":(
            status.HTTP_400_BAD_REQUEST,
            "Account currencies do not match",
        ),
        "INSUFFICIENT_FUNDS":(
            status.HTTP_409_CONFLICT,
             "Insufficient funds",
        ),
         "IDEMPOTENCY_CONFLICT":(
             status.HTTP_409_CONFLICT,
             "Idempotency key was already used for another transfer",
         ),
    }

@router.post("/",response_model=TransferRead,status_code=status.HTTP_201_CREATED,)
def create_transfer_endpoint(
    transfer_data: TransferCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ):

    result = create_transfer(
        transfer_data=transfer_data,
        idempotency_key=idempotency_key,
        db=db,
        current_user=current_user,
    )

    if isinstance(result,str):
        error_status, message = TRANSFER_ERROR_RESPONSES[result]

        raise HTTPException(
            status_code=error_status,
            detail=message
        )
    return result