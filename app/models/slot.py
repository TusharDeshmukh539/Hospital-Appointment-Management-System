from datetime import date, time

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import SlotStatus


class Slot(TimestampMixin, Base):

    __tablename__ = "slots"
    __table_args__ = (
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
