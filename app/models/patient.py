from datetime import date

from sqlalchemy import Date, String, Text, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    date_of_birth: Mapped[date | None] = mapped_column(Date)

    gender: Mapped[str | None] = mapped_column(
        Enum("MALE", "FEMALE", "OTHER", name="gender_enum")
    )

    blood_group: Mapped[str | None] = mapped_column(String(10))
    address: Mapped[str | None] = mapped_column(Text)

    user = relationship("User", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")