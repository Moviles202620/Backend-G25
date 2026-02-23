import re
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional

TITLE_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜáéíóúüÑñ ]+$")


class OfferCreateIn(BaseModel):
    title: str
    description: str
    category: Optional[str] = None
    value_cop: int
    duration_hours: int
    is_on_site: bool
    date_time: datetime

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Title must have at least 3 characters")
        if len(v) > 80:
            raise ValueError("Title max length is 80")
        if not TITLE_RE.match(v):
            raise ValueError("Title must contain only letters and spaces")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Description min length is 10")
        if len(v) > 1000:
            raise ValueError("Description max length is 1000")
        return v

    @field_validator("value_cop")
    @classmethod
    def validate_value(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("value_cop must be > 0")
        return v

    @field_validator("duration_hours")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("duration_hours must be > 0")
        return v


class OfferOut(BaseModel):
    id: int
    staff_id: int
    title: str
    description: str
    category: Optional[str]
    value_cop: int
    duration_hours: int
    is_on_site: bool
    date_time: datetime

    class Config:
        from_attributes = True
