"""Database access for availability_templates (the weekly schedule)."""
from datetime import time
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.availability_template import AvailabilityTemplate


def create(db: Session, doctor_id: int, weekday: int, start_time: time, end_time: time,
           slot_minutes: int) -> AvailabilityTemplate:
    template = AvailabilityTemplate(
        doctor_id=doctor_id,
        weekday=weekday,
        start_time=start_time,
        end_time=end_time,
        slot_minutes=slot_minutes,
    )
    db.add(template)
    db.flush()
    return template


def list_for_doctor(db: Session, doctor_id: int) -> list[AvailabilityTemplate]:
    query = (
        select(AvailabilityTemplate)
        .where(AvailabilityTemplate.doctor_id == doctor_id)
        .order_by(AvailabilityTemplate.weekday, AvailabilityTemplate.start_time)
    )
    return list(db.scalars(query).all())


def list_for_weekday(db: Session, doctor_id: int, weekday: int) -> list[AvailabilityTemplate]:
    query = select(AvailabilityTemplate).where(
        AvailabilityTemplate.doctor_id == doctor_id, AvailabilityTemplate.weekday == weekday
    )
    return list(db.scalars(query).all())


def get_for_doctor(db: Session, template_id: int, doctor_id: int) -> Optional[AvailabilityTemplate]:
    """Find a template only if it belongs to this doctor."""
    return db.scalar(
        select(AvailabilityTemplate).where(
            AvailabilityTemplate.id == template_id, AvailabilityTemplate.doctor_id == doctor_id
        )
    )


def delete(db: Session, template: AvailabilityTemplate) -> None:
    db.delete(template)
    db.flush()
