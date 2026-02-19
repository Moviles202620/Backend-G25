from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True)
    staff_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    title = Column(String(80), nullable=False)
    description = Column(String(1000), nullable=False)
    category = Column(String(100), nullable=True)

    value_cop = Column(Integer, nullable=False)
    duration_hours = Column(Integer, nullable=False)
    is_on_site = Column(Boolean, nullable=False, default=True)
    date_time = Column(DateTime(timezone=False), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
