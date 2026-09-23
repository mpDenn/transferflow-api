from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

class AccountCreate(BaseModel):

    currency: str = Field(default="GBP", min_length=3, max_length=3)

class AccountRead(BaseModel):

    id: int
    user_id: int
    account_number: str
    balance: Decimal
    currency: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
