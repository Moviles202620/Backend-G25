from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    department = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default="student")
    language = Column(String(2), nullable=False, default="es")
    is_dark_mode = Column(Boolean, nullable=False, default=False)
    # Isabella — Sprint 3: Coil — carnet image URL stored after Supabase Storage upload
    profile_picture = Column(String(500), nullable=True)
    # Isabella — Sprint 4: PaymentDocuments — RUT document URL after Supabase Storage upload
    rut_url = Column(String(500), nullable=True)
    # Isabella — Sprint 4: PaymentDocuments — cedula document URL after Supabase Storage upload
    cedula_url = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)