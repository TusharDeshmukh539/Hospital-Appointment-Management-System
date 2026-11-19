from datetime import datetime

from sqlalchemy import DateTime, Text, Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Appointment(Base):
    __tablename__ = "appointments"

    __table_args__ = (
        Index("idx_appointments_doctor_status", "doctor_id", "status"),
        Index("idx_appointments_patient", "patient_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    slot_id: Mapped[int] = mapped_column(
        ForeignKey("slots.id"),
        unique=True,
        nullable=False
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id"),
        nullable=False
    )

    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.id"),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "BOOKED",
            "COMPLETED",
            "CANCELLED",
            "NO_SHOW",
            name="appointment_status"
        ),
        default="BOOKED",
        nullable=False
    )

    booked_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime)
    reason: Mapped[str | None] = mapped_column(Text)

    slot = relationship("Slot", back_populates="appointment")
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")

    consultation = relationship(
        "Consultation",
        back_populates="appointment",
        uselist=False
    )