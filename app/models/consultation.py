from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import utc_now
from app.db.base import Base, TimestampMixin
from app.models.enums import AppointmentStatus


class Consultation(TimestampMixin, Base):
    """What happened during a COMPLETED appointment (clinical data - very sensitive)."""

    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(primary_key=True)
    # unique: an appointment can have at most one consultation record
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), unique=True)
    diagnosis: Mapped[str] = mapped_column(Text)
    prescription: Mapped[str] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    follow_up_date: Mapped[Optional[date]] = mapped_column(Date)

    appointment: Mapped["Appointment"] = relationship(back_populates="consultation")

    @property
    def doctor_name(self) -> str:
        return self.appointment.doctor.user.full_name

    @property
    def appointment_date(self) -> date:
        return self.appointment.slot.slot_date

