from sqlalchemy.orm import Session

from app.core.security import verify_password, hash_password
from app.models.user import User
from app.utils.exceptions import BadRequest, Unauthorized


def update_me(db: Session, user: User, name: str, department: str, language: str, is_dark_mode: bool) -> User:
    user.name = name
    user.department = department
    user.language = language
    user.is_dark_mode = is_dark_mode
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, current_password: str, new_password: str):
    if not verify_password(current_password, user.password_hash):
        raise Unauthorized("Current password is incorrect")

    if len(new_password) < 6:
        raise BadRequest("New password must be at least 6 characters")

    user.password_hash = hash_password(new_password)
    db.add(user)
    db.commit()
    db.refresh(user)
