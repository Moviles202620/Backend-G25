from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.core.config import settings
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.models.user import User
from app.utils.exceptions import BadRequest, Unauthorized


def _ensure_institutional_email(email: str):
    if not email.lower().endswith("@uniandes.edu.co"):
        raise BadRequest("Email must be institutional (@uniandes.edu.co)")


def login(db: Session, email: str, password: str):
    _ensure_institutional_email(email)

    user = db.query(User).filter(User.email == email.lower()).first()
    if not user or not verify_password(password, user.password_hash):
        raise Unauthorized("Invalid credentials")

    access = create_access_token(user.id, user.email)
    refresh = create_refresh_token(user.id, user.email)

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "department": user.department,
            "language": user.language,
            "is_dark_mode": user.is_dark_mode,
        },
    }


def refresh_access_token(refresh_token: str) -> str:
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub")
        email = payload.get("email")
        if not sub or not email:
            raise Unauthorized("Invalid refresh token")
        user_id = int(sub)
    except (JWTError, ValueError):
        raise Unauthorized("Invalid refresh token")

    # Si exp está vencido, jose lanza error y cae arriba.
    return create_access_token(user_id, email)
