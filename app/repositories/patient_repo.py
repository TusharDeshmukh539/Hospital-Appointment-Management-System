"""Database access for the patients table."""
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.patient import Patient
from app.models.user import User
from app.repositories.pagination import apply_order, paginate

SORT_COLUMNS = {
    "name": User.full_name,
    "date_of_birth": Patient.date_of_birth,
    "created_at": Patient.created_at,
}


def get_by_id(db: Session, patient_id: int) -> Optional[Patient]:
    return db.scalar(
        select(Patient).where(Patient.id == patient_id).options(joinedload(Patient.user))
    )


def get_by_user_id(db: Session, user_id: int) -> Optional[Patient]:
    return db.scalar(
        select(Patient).where(Patient.user_id == user_id).options(joinedload(Patient.user))
    )


def create(db: Session, user_id: int) -> Patient:
    patient = Patient(user_id=user_id)
    db.add(patient)
    db.flush()
    return patient


def list_paginated(db: Session, name: Optional[str], gender: Optional[str],
                   blood_group: Optional[str], sort_by: str, sort_order: str,
                   page: int, size: int):
    query = (
        select(Patient)
        .join(User, Patient.user_id == User.id)
        .options(joinedload(Patient.user))
    )
    if name:
        query = query.where(func.lower(User.full_name).like(f"%{name.lower()}%"))
    if gender:
        query = query.where(Patient.gender == gender)
    if blood_group:
        query = query.where(Patient.blood_group == blood_group)
    query = query.order_by(apply_order(SORT_COLUMNS[sort_by], sort_order), Patient.id)
    return paginate(db, query, page, size)
