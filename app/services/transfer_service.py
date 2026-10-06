from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.account import Account
from app.models.transfer import Transfer
from app.models.user import User
from app.schemas.transfer import TransferCreate
from datetime import datetime, timezone
from app.models.transfer import Transfer, TransferStatus
from decimal import Decimal

def _get_locked_accounts(transfer_data: TransferCreate, db: Session) ->list[Account]:

    accounts = db.execute(
            select(Account)
            .where(
                or_(
                    Account.id == transfer_data.from_account_id,
                    Account.account_number == transfer_data.to_account_number
                )
            )
            .order_by(Account.id)
            .with_for_update()
        ).scalars().all()

    return accounts

def _find_transfer_accounts(
        accounts: list[Account],
        transfer_data: TransferCreate,
        ) -> tuple[Account | None, Account | None]:

    from_account = next(
            (
                account
                for account in accounts
                if account.id == transfer_data.from_account_id
            ),
            None,
        )

    to_account = next(
            (
                account
                for account in accounts
                if account.account_number== transfer_data.to_account_number
            ),
            None,
        )

    return from_account, to_account

def _get_existing_transfer(db: Session, idempotency_key: str) -> Transfer | None:
    existing_transfer = db.execute(
            select(Transfer).where(Transfer.idempotency_key == idempotency_key)
            ).scalars().first()

    return existing_transfer

def _validate_transfer_rules(
        from_account: Account,
        to_account: Account,
        amount: Decimal
) -> str | None:

    if from_account.id == to_account.id:
        return "SAME_ACCOUNT"

    if not from_account.is_active or not to_account.is_active:
        return "ACCOUNT_INACTIVE"

    if from_account.currency != to_account.currency:
        return "CURRENCY_MISMATCH"

    if from_account.balance < amount:
        return "INSUFFICIENT_FUNDS"

    return None

def _apply_transfer(
        from_account: Account,
        to_account: Account,
        transfer_data: TransferCreate,
        idempotency_key: str,
) -> Transfer:

    from_account.balance -= transfer_data.amount
    to_account.balance += transfer_data.amount

    transfer = Transfer(
        from_account_id=from_account.id,
        to_account_id=to_account.id,
        amount=transfer_data.amount,
        currency=from_account.currency,
        status=TransferStatus.COMPLETED,
        idempotency_key=idempotency_key,
        completed_at=datetime.now(timezone.utc),
    )
    return transfer

def _check_idempotency(
        db: Session,
        idempotency_key: str,
        from_account: Account,
        to_account: Account,
        transfer_data: TransferCreate
) -> Transfer | str | None:

    existing_transfer = _get_existing_transfer(db, idempotency_key)
    if not existing_transfer:
        return None

    same_transfer = _is_same_transfer(
        existing_transfer,
        from_account,
        to_account,
        transfer_data,
        )

    if same_transfer:
        return existing_transfer

    return "IDEMPOTENCY_CONFLICT"

def _is_same_transfer(
        transfer: Transfer,
        from_account: Account,
        to_account: Account,
        transfer_data: TransferCreate,
    ) -> bool:
    return (
        transfer.from_account_id == from_account.id
        and transfer.to_account_id == to_account.id
        and transfer.amount == transfer_data.amount
    )

def create_transfer(
        transfer_data: TransferCreate,
        idempotency_key: str,
        current_user: User,
        db:Session,
    ) -> Transfer | str:

    accounts = _get_locked_accounts(transfer_data, db)

    from_account, to_account = _find_transfer_accounts(accounts, transfer_data)

    if not from_account or from_account.user_id != current_user.id:
        return "FROM_ACCOUNT_NOT_FOUND"

    if not to_account:
        return "TO_ACCOUNT_NOT_FOUND"

    idempotency_result = _check_idempotency(
        db,
        idempotency_key,
        from_account,
        to_account,
        transfer_data
    )

    if idempotency_result is not None:
        return idempotency_result

    validation_error = _validate_transfer_rules(from_account, to_account, transfer_data.amount)
    if validation_error:
        return validation_error

    transfer = _apply_transfer(
        from_account,
        to_account,
        transfer_data,
        idempotency_key,
    )

    db.add(transfer)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        idempotency_result = _check_idempotency(
                db,
                idempotency_key,
                from_account,
                to_account,
                transfer_data
            )

        if idempotency_result is not None:
            return idempotency_result

        raise

    db.refresh(transfer)
    return transfer





