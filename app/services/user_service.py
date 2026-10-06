from app.models.user import User
from sqlalchemy import select
from app.security import hash_password

def create_user(user_data, db):

    existing_user = db.execute(
        select(User).where(User.email == user_data.email)
        ).scalars().first()

    if existing_user:
        return "user_already_exists"

    new_user = User(
        full_name = user_data.full_name,
        email = str(user_data.email),
        password_hash = hash_password(user_data.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
