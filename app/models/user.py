from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('ADMIN', 'DOCTOR', 'PATIENT')", name="role_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))  # bcrypt hash, never the password
    full_name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    role: Mapped[str] = mapped_column(String(20), index=True)
    # Soft delete: a deactivated user is kept in the database but cannot log in.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    doctor_profile: Mapped[Optional["Doctor"]] = relationship(back_populates="user", uselist=False)
    patient_profile: Mapped[Optional["Patient"]] = relationship(back_populates="user", uselist=False)
