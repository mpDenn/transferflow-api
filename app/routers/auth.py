from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserLogin, Token
from app.security import verify_password, create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["login"],
)

@router.post("/login", response_model=Token)
def post_user(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.execute(
        select(User).where(User.email == user_data.email)
        ).scalars().first()

    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(str(user.id))

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }