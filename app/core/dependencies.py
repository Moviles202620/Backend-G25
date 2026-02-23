from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User
from app.utils.exceptions import Unauthorized

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub")
        email = payload.get("email")
        if not sub or not email:
            raise Unauthorized("Invalid token")
        user_id = int(sub)
    except (JWTError, ValueError):
        raise Unauthorized("Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise Unauthorized("User not found")
    return user

