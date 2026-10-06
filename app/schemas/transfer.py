from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.models.transfer import TransferStatus

class TransferCreate(BaseModel):
    from_account_id: int
    to_account_number: str = Field(min_length=12, max_length=12)
    amount: Decimal = Field(gt=0, max_digits= 18, decimal_places=2)

class TransferRead(BaseModel):
    id: int
    from_account_id: int
    to_account_id: int
    amount: Decimal
    currency: str
    status: TransferStatus
    created_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

















