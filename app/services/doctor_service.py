"""Business logic for doctors and their profiles."""
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging_config import audit_log
from app.core.security import hash_password
from app.exceptions import ConflictError, NotFoundError
from app.models.doctor import Doctor
from app.models.enums import Role
from app.models.user import User
from app.repositories import doctor_repo, speciality_repo, user_repo
from app.schemas.common import make_page
from app.schemas.doctor import DoctorCreate, DoctorUpdate


def get_my_doctor_profile(db: Session, user: User) -> Doctor:
    """Find the doctor profile of the logged-in doctor.

    Other services call this too, so a doctor can only ever work with
    HIS OWN profile - never somebody else's.
    """
    doctor = doctor_repo.get_by_user_id(db, user.id)
    if doctor is None:
        raise NotFoundError("Doctor profile not found")
    return doctor


def create_doctor(db: Session, admin: User, data: DoctorCreate) -> Doctor:
    """Admin creates a doctor: a login account (role DOCTOR) + a doctor profile."""
    if user_repo.get_by_email(db, data.email):
        raise ConflictError("An account with this email already exists")
    if speciality_repo.get_by_id(db, data.speciality_id) is None:
        raise NotFoundError("Speciality not found")
    if doctor_repo.get_by_registration_no(db, data.registration_no):
        raise ConflictError("A doctor with this registration number already exists")

    user = user_repo.create(
        db,
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        phone=data.phone,
        role=Role.DOCTOR.value,
    )
    doctor = doctor_repo.create(
        db,
        user_id=user.id,
        speciality_id=data.speciality_id,
        registration_no=data.registration_no,
        qualification=data.qualification,
        experience_years=data.experience_years,
        consultation_fee=data.consultation_fee,
    )
    db.commit()
    audit_log("doctor.create", user_id=admin.id, doctor_id=doctor.id)
    return doctor


def list_doctors(db: Session, speciality: Optional[str], name: Optional[str], sort_by: str,
                 sort_order: str, page: int, size: int) -> dict:
    items, total = doctor_repo.list_paginated(db, speciality, name, sort_by, sort_order, page, size)
    return make_page(items, total, page, size)


def get_doctor(db: Session, doctor_id: int) -> Doctor:
    doctor = doctor_repo.get_by_id(db, doctor_id)
    # Deactivated doctors are treated as "not found" for everybody.
    if doctor is None or not doctor.is_active:
        raise NotFoundError("Doctor not found")
    return doctor


def update_my_profile(db: Session, user: User, data: DoctorUpdate) -> Doctor:
    doctor = get_my_doctor_profile(db, user)

    # exclude_unset=True -> only the fields the client really sent
    changes = data.model_dump(exclude_unset=True)
    if "speciality_id" in changes and changes["speciality_id"] is not None:
        if speciality_repo.get_by_id(db, changes["speciality_id"]) is None:
            raise NotFoundError("Speciality not found")

    for field_name, value in changes.items():
        if value is not None:  # ignore explicit nulls: these columns are required
            setattr(doctor, field_name, value)
    db.commit()

    audit_log("doctor.update_profile", user_id=user.id, doctor_id=doctor.id)
    # Reload so the speciality relationship reflects a changed speciality_id.
    return doctor_repo.get_by_id(db, doctor.id)
