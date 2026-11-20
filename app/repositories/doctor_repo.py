"""Database access for the doctors table."""
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.doctor import Doctor
from app.models.speciality import Speciality
from app.models.user import User
from app.repositories.pagination import apply_order, paginate

SORT_COLUMNS = {
    "name": User.full_name,
    "fee": Doctor.consultation_fee,
    "experience": Doctor.experience_years,
}


def get_by_id(db: Session, doctor_id: int) -> Optional[Doctor]:
    return db.scalar(
        select(Doctor)
        .where(Doctor.id == doctor_id)
        # joinedload loads the user and speciality in the SAME query (avoids extra queries)
        .options(joinedload(Doctor.user), joinedload(Doctor.speciality))
    )


def get_by_user_id(db: Session, user_id: int) -> Optional[Doctor]:
    return db.scalar(
        select(Doctor)
        .where(Doctor.user_id == user_id)
        .options(joinedload(Doctor.user), joinedload(Doctor.speciality))
    )


def get_by_registration_no(db: Session, registration_no: str) -> Optional[Doctor]:
    return db.scalar(select(Doctor).where(Doctor.registration_no == registration_no))


def list_paginated(db: Session, speciality: Optional[str], name: Optional[str],
                   sort_by: str, sort_order: str, page: int, size: int):
    # We join users and specialities so we can filter and sort by their columns.
    query = (
        select(Doctor)
        .join(User, Doctor.user_id == User.id)
        .join(Speciality, Doctor.speciality_id == Speciality.id)
        .where(User.is_active.is_(True))  # hide deactivated doctors from patients
        .options(joinedload(Doctor.user), joinedload(Doctor.speciality))
    )
    if speciality:
        query = query.where(func.lower(Speciality.name).like(f"%{speciality.lower()}%"))
    if name:
        query = query.where(func.lower(User.full_name).like(f"%{name.lower()}%"))
    query = query.order_by(apply_order(SORT_COLUMNS[sort_by], sort_order), Doctor.id)
    return paginate(db, query, page, size)


def create(db: Session, user_id: int, speciality_id: int, registration_no: str,
           qualification: str, experience_years: int, consultation_fee: Decimal) -> Doctor:
    doctor = Doctor(
        user_id=user_id,
        speciality_id=speciality_id,
        registration_no=registration_no,
        qualification=qualification,
        experience_years=experience_years,
        consultation_fee=consultation_fee,
    )
    db.add(doctor)
    db.flush()
    return doctor
