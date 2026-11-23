from datetime import date
from typing import Optional

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.slot import Slot
from app.models.doctor import Doctor
from app.models.speciality import Speciality
from app.models.enums import AppointmentStatus
from app.models.user import User


def _appointment_join_condition(base_condition, from_date: Optional[date], to_date: Optional[date]):
    if from_date is None and to_date is None:
        return base_condition
    slot_ids = select(Slot.id)
    if from_date is not None:
        slot_ids = slot_ids.where(Slot.slot_date >= from_date)
    if to_date is not None:
        slot_ids = slot_ids.where(Slot.slot_date <= to_date)
    return and_(base_condition, Appointment.slot_id.in_(slot_ids))


def _count_status(status: AppointmentStatus):
    return func.coalesce(func.sum(case((Appointment.status == status.value, 1), else_=0)), 0)


def doctor_load(db: Session, from_date: Optional[date], to_date: Optional[date]) -> list[dict]:
    query = (
        select(
            Doctor.id.label("doctor_id"),
            User.full_name.label("doctor_name"),
            Speciality.name.label("speciality_name"),
            func.count(Appointment.id).label("total"),
            _count_status(AppointmentStatus.BOOKED).label("booked"),
            _count_status(AppointmentStatus.COMPLETED).label("completed"),
            _count_status(AppointmentStatus.CANCELLED).label("cancelled"),
            _count_status(AppointmentStatus.NO_SHOW).label("no_show"),
        )
        .select_from(Doctor)
        .join(User, Doctor.user_id == User.id)
        .join(Speciality, Doctor.speciality_id == Speciality.id)
        .outerjoin(
            Appointment,
            _appointment_join_condition(Appointment.doctor_id == Doctor.id, from_date, to_date),
        )
        .group_by(Doctor.id, User.full_name, Speciality.name)
        .order_by(func.count(Appointment.id).desc(), Doctor.id)
    )
    return [dict(row._mapping) for row in db.execute(query).all()]


def speciality_demand(db: Session, from_date: Optional[date], to_date: Optional[date]) -> list[dict]:
    query = (
        select(
            Speciality.id.label("speciality_id"),
            Speciality.name.label("speciality_name"),
            func.count(Appointment.id).label("appointments"),
        )
        .select_from(Speciality)
        .outerjoin(Doctor, Doctor.speciality_id == Speciality.id)
        .outerjoin(
            Appointment,
            _appointment_join_condition(Appointment.doctor_id == Doctor.id, from_date, to_date),
        )
        .group_by(Speciality.id, Speciality.name)
        .order_by(func.count(Appointment.id).desc(), Speciality.name)
    )
    return [dict(row._mapping) for row in db.execute(query).all()]
