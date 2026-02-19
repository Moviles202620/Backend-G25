from pydantic import BaseModel, EmailStr
from typing import Literal

Status = Literal["pending", "accepted", "rejected"]


class ApplicationOut(BaseModel):
    id: int
    offer_id: int
    student_name: str
    student_email: EmailStr
    status: Status

    class Config:
        from_attributes = True


class UpdateStatusIn(BaseModel):
    status: Status
