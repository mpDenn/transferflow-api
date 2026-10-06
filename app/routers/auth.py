from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import UserLogin, Token
from app.services.auth_service import post_user

router = APIRouter(
    prefix="/auth",
    tags=["login"],
)

@router.post("/login", response_model=Token)
def post_user_endpoint(user_data: UserLogin, db: Session = Depends(get_db)):

    login_user = post_user(user_data, db)

    if login_user == "user_or_passwrod_wrong":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    return login_user