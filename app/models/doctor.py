from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    speciality_id: Mapped[int] = mapped_column(
        ForeignKey("specialities.id"),
        nullable=False
    )

    registration_no: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    qualification: Mapped[str | None] = mapped_column(String(255))
    experience_years: Mapped[int | None] = mapped_column(Integer)

    consultation_fee: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    user = relationship("User", back_populates="doctor")
    speciality = relationship("Speciality", back_populates="doctors")

    availability_templates = relationship(
        "AvailabilityTemplate",
        back_populates="doctor",
        cascade="all, delete-orphan"
    )

    slots = relationship(
        "Slot",
        back_populates="doctor",
        cascade="all, delete-orphan"
    )

    appointments = relationship("Appointment", back_populates="doctor")