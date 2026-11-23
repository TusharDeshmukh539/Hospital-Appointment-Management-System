from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging_config import audit_log
from app.exceptions import NotFoundError
from app.models.patient import Patient
from app.models.user import User
from app.repositories import patient_repo
from app.schemas.common import make_page
from app.schemas.patient import PatientUpdate


def get_my_patient_profile(db: Session, user: User) -> Patient:
    patient = patient_repo.get_by_user_id(db, user.id)
    if patient is None:
        raise NotFoundError("Patient profile not found")
    return patient


def update_my_profile(db: Session, user: User, data: PatientUpdate) -> Patient:
    patient = get_my_patient_profile(db, user)
    changes = data.model_dump(exclude_unset=True)

    # full_name and phone live in the users table, the rest in the patients table.
    for field_name in ("full_name", "phone"):
        if field_name in changes:
            setattr(user, field_name, changes.pop(field_name))
    for field_name, value in changes.items():
        setattr(patient, field_name, value)
    db.commit()

    audit_log("patient.update_profile", user_id=user.id, patient_id=patient.id)
    return patient_repo.get_by_id(db, patient.id)


def list_patients(db: Session, name: Optional[str], gender: Optional[str],
                  blood_group: Optional[str], sort_by: str, sort_order: str,
                  page: int, size: int) -> dict:
    items, total = patient_repo.list_paginated(
        db, name, gender, blood_group, sort_by, sort_order, page, size
    )
    return make_page(items, total, page, size)
