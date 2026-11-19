from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import utc_now
from app.db.base import Base, TimestampMixin
from app.models.enums import AppointmentStatus


class Appointment(TimestampMixin, Base):
    __tablename__ = "appointments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('BOOKED', 'COMPLETED', 'CANCELLED', 'NO_SHOW')", name="status_valid"
        ),
        # Indexes requested in the case study (speed up the doctor's and patient's lists).
        Index("ix_appointments_doctor_id_status", "doctor_id", "status"),
        Index("ix_appointments_patient_id", "patient_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slot_id: Mapped[int] = mapped_column(ForeignKey("slots.id"), index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    status: Mapped[str] = mapped_column(String(20), default=AppointmentStatus.BOOKED.value)
    booked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    reason: Mapped[Optional[str]] = mapped_column(String(255))  # reason for the visit

    slot: Mapped["Slot"] = relationship()
    patient: Mapped["Patient"] = relationship()
    doctor: Mapped["Doctor"] = relationship()
    consultation: Mapped[Optional["Consultation"]] = relationship(
        back_populates="appointment", uselist=False
    )

    # Convenience properties used by the response schemas.
    @property
    def doctor_name(self) -> str:
        return self.doctor.user.full_name

    @property
    def patient_name(self) -> str:
        return self.patient.user.full_name

    @property
    def slot_date(self) -> date:
        return self.slot.slot_date

    @property
    def start_time(self) -> time:
        return self.slot.start_time

    @property
    def end_time(self) -> time:
        return self.slot.end_time
