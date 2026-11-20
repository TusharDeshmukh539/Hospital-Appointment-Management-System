"""Business logic for specialities (master data maintained by admins)."""
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging_config import audit_log
from app.exceptions import ConflictError, NotFoundError
from app.models.doctor import Speciality
from app.models.user import User
from app.repositories import speciality_repo
from app.schemas.common import make_page
from app.schemas.speciality import SpecialityCreate, SpecialityUpdate


def create_speciality(db: Session, admin: User, data: SpecialityCreate) -> Speciality:
    if speciality_repo.get_by_name(db, data.name):
        raise ConflictError("This speciality already exists")
    speciality = speciality_repo.create(db, data.name)
    db.commit()
    audit_log("speciality.create", user_id=admin.id, speciality_id=speciality.id)
    return speciality


def list_specialities(db: Session, name: Optional[str], sort_by: str, sort_order: str,
                      page: int, size: int) -> dict:
    items, total = speciality_repo.list_paginated(db, name, sort_by, sort_order, page, size)
    return make_page(items, total, page, size)


def update_speciality(db: Session, admin: User, speciality_id: int, data: SpecialityUpdate) -> Speciality:
    speciality = speciality_repo.get_by_id(db, speciality_id)
    if speciality is None:
        raise NotFoundError("Speciality not found")

    other = speciality_repo.get_by_name(db, data.name)
    if other is not None and other.id != speciality.id:
        raise ConflictError("This speciality already exists")

    speciality.name = data.name
    db.commit()
    audit_log("speciality.update", user_id=admin.id, speciality_id=speciality.id)
    return speciality


def delete_speciality(db: Session, admin: User, speciality_id: int) -> None:
    speciality = speciality_repo.get_by_id(db, speciality_id)
    if speciality is None:
        raise NotFoundError("Speciality not found")
    # A speciality that doctors still use must not disappear.
    if speciality_repo.count_doctors(db, speciality_id) > 0:
        raise ConflictError("Speciality is used by doctors and cannot be deleted")

    speciality_repo.delete(db, speciality)
    db.commit()
    audit_log("speciality.delete", user_id=admin.id, speciality_id=speciality_id)
