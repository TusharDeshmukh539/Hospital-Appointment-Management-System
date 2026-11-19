from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.doctor import Doctor

class Speciality(TimestampMixin, Base):
    """A medical speciality such as Cardiology (master data)."""

    __tablename__ = "specialities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    doctors: Mapped[list["Doctor"]] = relationship(back_populates="speciality")
        