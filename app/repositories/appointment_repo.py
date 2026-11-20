"""Database access for the appointments table."""
from datetime import date
from typing import Optional

from sqlalchemy import and_, func, not_, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.utils import utc_now_naive
from app.models.appointment import Appointment
from app.models.slot import Slot
from app.models.doctor import Doctor
from app.models.enums import AppointmentStatus
from app.models.patient import Patient
from app.repositories.pagination import apply_order, paginate

SORT_COLUMNS = {"date": Slot.slot_date, "booked_at": Appointment.booked_at}


def _load_options():
    """Load everything the AppointmentOut schema needs in one go."""
    return (
        joinedload(Appointment.slot),
        joinedload(Appointment.doctor).joinedload(Doctor.user),
        joinedload(Appointment.patient).joinedload(Patient.user),
    )


def create(db: Session, slot_id: int, patient_id: int, doctor_id: int,
           reason: Optional[str]) -> Appointment:
    appointment = Appointment(
        slot_id=slot_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        status=AppointmentStatus.BOOKED.value,
        reason=reason,
    )
    db.add(appointment)
    db.flush()
    return appointment


def get_for_patient(db: Session, appointment_id: int, patient_id: int) -> Optional[Appointment]:
    """Find an appointment ONLY if it belongs to this patient (ownership check)."""
    return db.scalar(
        select(Appointment)
        .where(Appointment.id == appointment_id, Appointment.patient_id == patient_id)
        .options(*_load_options())
    )


def get_for_doctor(db: Session, appointment_id: int, doctor_id: int) -> Optional[Appointment]:
    """Find an appointment ONLY if it belongs to this doctor (ownership check)."""
    return db.scalar(
        select(Appointment)
        .where(Appointment.id == appointment_id, Appointment.doctor_id == doctor_id)
        .options(*_load_options())
    )


def patient_has_active_on_date(db: Session, patient_id: int, doctor_id: int, slot_date: date,
                               exclude_appointment_id: Optional[int] = None) -> bool:
    """Does the patient already hold a BOOKED appointment with this doctor on this date?"""
    query = (
        select(func.count(Appointment.id))
        .select_from(Appointment)
        .join(Slot, Appointment.slot_id == Slot.id)
        .where(
            Appointment.patient_id == patient_id,
            Appointment.doctor_id == doctor_id,
            Appointment.status == AppointmentStatus.BOOKED.value,
            Slot.slot_date == slot_date,
        )
    )
    if exclude_appointment_id is not None:
        query = query.where(Appointment.id != exclude_appointment_id)
    return (db.scalar(query) or 0) > 0


def list_for_patient(db: Session, patient_id: int, when: str, status: Optional[str],
                     sort_by: str, sort_order: str, page: int, size: int):
    """List a patient's appointments.

    when = "upcoming": BOOKED and the slot has not started yet
    when = "past":     everything else (finished, cancelled or already started)
    when = "all":      no time filter
    """
    now = utc_now_naive()
    slot_is_in_future = or_(
        Slot.slot_date > now.date(),
        and_(Slot.slot_date == now.date(), Slot.start_time >= now.time()),
    )
    is_upcoming = and_(slot_is_in_future, Appointment.status == AppointmentStatus.BOOKED.value)

    query = (
        select(Appointment)
        .join(Slot, Appointment.slot_id == Slot.id)
        .where(Appointment.patient_id == patient_id)
        .options(*_load_options())
    )
    if when == "upcoming":
        query = query.where(is_upcoming)
    elif when == "past":
        query = query.where(not_(is_upcoming))
    if status:
        query = query.where(Appointment.status == status)
    query = query.order_by(apply_order(SORT_COLUMNS[sort_by], sort_order), Slot.start_time, Appointment.id)
    return paginate(db, query, page, size)


def list_for_doctor_on_date(db: Session, doctor_id: int, slot_date: date, status: Optional[str],
                            sort_order: str, page: int, size: int):
    """List a doctor's appointments on one day, ordered by time."""
    query = (
        select(Appointment)
        .join(Slot, Appointment.slot_id == Slot.id)
        .where(Appointment.doctor_id == doctor_id, Slot.slot_date == slot_date)
        .options(*_load_options())
    )
    if status:
        query = query.where(Appointment.status == status)
    query = query.order_by(apply_order(Slot.start_time, sort_order), Appointment.id)
    return paginate(db, query, page, size)
