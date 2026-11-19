from datetime import date, time

from sqlalchemy import Date, Time, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Slot(Base):
    __tablename__ = "slots"

    __table_args__ = (
        UniqueConstraint(
            "doctor_id",
            "slot_date",
            "start_time",
            name="uq_doctor_slot"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.id"),
        nullable=False
    )

    slot_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    status: Mapped[str] = mapped_column(
        Enum("FREE", "BOOKED", "BLOCKED", name="slot_status"),
        default="FREE",
        nullable=False
    )

    doctor = relationship("Doctor", back_populates="slots")
    appointment = relationship(
        "Appointment",
        back_populates="slot",
        uselist=False
    )