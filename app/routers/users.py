from fastapi import APIRouter, Depends
from app.schemas.user import UserCreate, UserRead
from sqlalchemy.orm import Session
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from app.database import get_db
from app.security import hash_password


router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.post("/", response_model= UserRead, status_code= 201)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):

    existing_user = db.execute(
        select(User).where(User.email == user_data.email)
        ).scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    new_user = User(
        full_name = user_data.full_name,
        email = str(user_data.email),
        password_hash = hash_password(user_data.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user