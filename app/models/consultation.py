from datetime import date

from sqlalchemy import Date, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Consultation(Base):
    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(primary_key=True)

    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id"),
        unique=True,
        nullable=False
    )

    diagnosis: Mapped[str | None] = mapped_column(Text)
    prescription: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    follow_up_date: Mapped[date | None] = mapped_column(Date)

    appointment = relationship(
        "Appointment",
        back_populates="consultation"
    )