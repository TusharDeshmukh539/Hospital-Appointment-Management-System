"""availability_templates and slots tables."""
from datetime import date, time

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import SlotStatus


class AvailabilityTemplate(TimestampMixin, Base):
    """A repeating weekly schedule, e.g. 'every Monday 09:00-13:00 in 30 minute slots'."""

    __tablename__ = "availability_templates"
    __table_args__ = (
        CheckConstraint("weekday >= 0 AND weekday <= 6", name="weekday_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    weekday: Mapped[int] = mapped_column(Integer)  # 0 = Monday ... 6 = Sunday
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    slot_minutes: Mapped[int] = mapped_column(Integer)  # length of one slot


class Slot(TimestampMixin, Base):
    """One bookable time slot of one doctor on one date."""

    __tablename__ = "slots"
    __table_args__ = (
        # The primary defence against double booking: the database will never
        # allow two slots with the same doctor, date and start time.
        UniqueConstraint("doctor_id", "slot_date", "start_time"),
        CheckConstraint("status IN ('FREE', 'BOOKED', 'BLOCKED')", name="status_valid"),
        Index("ix_slots_doctor_id_slot_date", "doctor_id", "slot_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    slot_date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    status: Mapped[str] = mapped_column(String(10), default=SlotStatus.FREE.value)

    doctor: Mapped["Doctor"] = relationship()
