from sqlalchemy import select
from app.models.user import User
from app.security import verify_password, create_access_token

def post_user(user_data, db):
    user = db.execute(
        select(User).where(User.email == user_data.email)
        ).scalars().first()

    if not user or not verify_password(user_data.password, user.password_hash):
       return "user_or_passwrod_wrong"

    access_token = create_access_token(str(user.id))

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }