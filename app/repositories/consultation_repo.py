"""Database access for the consultations table."""
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.appointment import Appointment
from app.models.consultation import Consultation
from app.models.slot import Slot
from app.models.doctor import Doctor
from app.repositories.pagination import apply_order, paginate


def _load_options():
    return (
        joinedload(Consultation.appointment).joinedload(Appointment.slot),
        joinedload(Consultation.appointment).joinedload(Appointment.doctor).joinedload(Doctor.user),
    )


def get_by_appointment_id(db: Session, appointment_id: int) -> Optional[Consultation]:
    return db.scalar(
        select(Consultation)
        .where(Consultation.appointment_id == appointment_id)
        .options(*_load_options())
    )


def create(db: Session, appointment_id: int, diagnosis: str, prescription: str,
           notes: Optional[str], follow_up_date: Optional[date]) -> Consultation:
    consultation = Consultation(
        appointment_id=appointment_id,
        diagnosis=diagnosis,
        prescription=prescription,
        notes=notes,
        follow_up_date=follow_up_date,
    )
    db.add(consultation)
    db.flush()
    return consultation


def list_for_patient(db: Session, patient_id: int, doctor_id: Optional[int],
                     from_date: Optional[date], to_date: Optional[date],
                     sort_order: str, page: int, size: int):
    """A patient's own consultations (the patient_id filter is always applied)."""
    query = (
        select(Consultation)
        .join(Appointment, Consultation.appointment_id == Appointment.id)
        .join(Slot, Appointment.slot_id == Slot.id)
        .where(Appointment.patient_id == patient_id)
        .options(*_load_options())
    )
    if doctor_id is not None:
        query = query.where(Appointment.doctor_id == doctor_id)
    if from_date is not None:
        query = query.where(Slot.slot_date >= from_date)
    if to_date is not None:
        query = query.where(Slot.slot_date <= to_date)
    query = query.order_by(apply_order(Slot.slot_date, sort_order), Consultation.id)
    return paginate(db, query, page, size)
