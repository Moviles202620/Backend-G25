from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.user import UserOut, UserUpdateIn, ChangePasswordIn
from app.services.user_service import update_me, change_password

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut)
def update_profile(
    payload: UserUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = update_me(db, current_user, payload.name, payload.department, payload.language, payload.is_dark_mode)
    return user


@router.put("/change-password")
def change_password_route(
    payload: ChangePasswordIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # confirm_password ya se valida en schema
    change_password(db, current_user, payload.current_password, payload.new_password)
    return {"detail": "Password updated successfully"}
