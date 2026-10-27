import enum

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class EntryType(str, enum.Enum):
    DEBIT = "debit"
    CREDIT = "credit"

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    transfer_id: Mapped[int] = mapped_column(ForeignKey("transfers.id"))
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    entry_type: Mapped[EntryType] = mapped_column(Enum(EntryType), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    create_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
        )