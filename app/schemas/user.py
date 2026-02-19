import re
from pydantic import BaseModel, EmailStr, field_validator
from typing import Literal

DEPARTMENTS = Literal["Ingeniería", "Ciencias Sociales", "Ciencias Básicas", "Administrativo", "Artes", "Deporte"]
LANGS = Literal["es", "en"]

NAME_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜáéíóúüÑñ ]+$")


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    department: str
    language: str
    is_dark_mode: bool

    class Config:
        from_attributes = True


class UserUpdateIn(BaseModel):
    name: str
    department: DEPARTMENTS
    language: LANGS
    is_dark_mode: bool

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Name must have at least 3 characters")
        if not NAME_RE.match(v):
            raise ValueError("Name must contain only letters and spaces")
        return v


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("New password must be at least 6 characters")
        return v

    @field_validator("confirm_password")
    @classmethod
    def validate_confirm(cls, v: str, info):
        new_password = info.data.get("new_password")
        if new_password and v != new_password:
            raise ValueError("confirm_password must match new_password")
        return v
