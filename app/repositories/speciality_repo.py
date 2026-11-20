"""Database access for the specialities table."""
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.doctor import Doctor, Speciality
from app.repositories.pagination import apply_order, paginate

# Allowed values for ?sort_by= (a whitelist: users can never inject column names).
SORT_COLUMNS = {"name": Speciality.name, "id": Speciality.id}


def get_by_id(db: Session, speciality_id: int) -> Optional[Speciality]:
    return db.get(Speciality, speciality_id)


def get_by_name(db: Session, name: str) -> Optional[Speciality]:
    """Case-insensitive lookup, so 'cardiology' finds 'Cardiology'."""
    return db.scalar(select(Speciality).where(func.lower(Speciality.name) == name.lower()))


def list_paginated(db: Session, name: Optional[str], sort_by: str, sort_order: str,
                   page: int, size: int):
    query = select(Speciality)
    if name:
        query = query.where(func.lower(Speciality.name).like(f"%{name.lower()}%"))
    query = query.order_by(apply_order(SORT_COLUMNS[sort_by], sort_order), Speciality.id)
    return paginate(db, query, page, size)


def create(db: Session, name: str) -> Speciality:
    speciality = Speciality(name=name)
    db.add(speciality)
    db.flush()
    return speciality


def delete(db: Session, speciality: Speciality) -> None:
    db.delete(speciality)
    db.flush()


def count_doctors(db: Session, speciality_id: int) -> int:
    return db.scalar(select(func.count(Doctor.id)).where(Doctor.speciality_id == speciality_id)) or 0
