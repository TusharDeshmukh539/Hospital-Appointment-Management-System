from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, TimestampMixin
from app.models.speciality import Speciality
from app.models.user import User


class Doctor(TimestampMixin, Base):
    """Doctor profile. The login details live in the linked users row."""
    
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    speciality_id: Mapped[int] = mapped_column(ForeignKey("specialities.id"), index=True)
    registration_no: Mapped[str] = mapped_column(String(50), unique=True)
    qualification: Mapped[str] = mapped_column(String(200))
    experience_years: Mapped[int] = mapped_column(Integer)
    # Money is always Numeric(12, 2) - never float (floats have rounding errors).
    consultation_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    user: Mapped["User"] = relationship(back_populates="doctor_profile")
    speciality: Mapped["Speciality"] = relationship(back_populates="doctors")

    @property
    def full_name(self) -> str:
        return self.user.full_name

    @property
    def speciality_name(self) -> str:
        return self.speciality.name

    @property
    def is_active(self) -> bool:
        return self.user.is_active
