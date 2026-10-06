from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from app.database import Base

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

class TransferStatus(str, PyEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class Transfer(Base):
    __tablename__ = "transfers"
    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="ck_transfers_amount_positive",
        ),
        CheckConstraint(
            "from_account_id != to_account_id",
            name="ck_transfers_accounts_different",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    from_account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id"),
        index=True
    )
    to_account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id"),
        index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18,2))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[TransferStatus] = mapped_column(
        SQLEnum(TransferStatus,
                name="transfer_status",
                values_callable=lambda enum_class: [
                    status.value for status in enum_class
                    ],
                ),
        default=TransferStatus.PENDING,
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )