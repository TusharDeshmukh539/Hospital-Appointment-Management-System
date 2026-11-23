from datetime import time

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class AvailabilityTemplate(TimestampMixin, Base):
    """A repeating weekly schedule, e.g. 'every Monday 09:00-13:00 in 30 minute slots'."""

    __tablename__ = "availability_templates"
    __table_args__ = (
        CheckConstraint("weekday >= 0 AND weekday <= 6", name="weekday_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), index=True)
    weekday: Mapped[int] = mapped_column(Integer)  
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    slot_minutes: Mapped[int] = mapped_column(Integer)  