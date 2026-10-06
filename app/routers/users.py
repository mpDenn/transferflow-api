from app.schemas.user import UserCreate, UserRead
from sqlalchemy.orm import Session
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.dependencies import get_current_user
from app.services.user_service import create_user
router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.post("/", response_model= UserRead, status_code= 201)
def create_user_endpoint(
        user_data: UserCreate,
        db: Session = Depends(get_db)
        ):

    new_user = create_user(user_data, db)

    if new_user == "user_already_exists":
        raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

    return new_user

@router.get("/me", response_model=UserRead)
def get_me(me: User = Depends(get_current_user)):
    return me