"""Business logic for consultations (diagnosis, prescription, follow-up).

Clinical records are visible ONLY to the patient concerned and the assigned doctor.
We never log diagnosis/prescription text - only ids.
"""
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging_config import audit_log
from app.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.appointment import Consultation
from app.models.enums import AppointmentStatus, Role
from app.models.user import User
from app.repositories import appointment_repo, consultation_repo
from app.schemas.common import make_page
from app.schemas.consultation import ConsultationCreate
from app.services.doctor_service import get_my_doctor_profile
from app.services.patient_service import get_my_patient_profile


def record_consultation(db: Session, user: User, appointment_id: int,
                        data: ConsultationCreate) -> Consultation:
    doctor = get_my_doctor_profile(db, user)
    # Ownership check: only the assigned doctor finds the appointment.
    appointment = appointment_repo.get_for_doctor(db, appointment_id, doctor.id)
    if appointment is None:
        raise NotFoundError("Appointment not found")

    # Business rule 6: only for COMPLETED appointments
    if appointment.status != AppointmentStatus.COMPLETED.value:
        raise ConflictError("A consultation can only be recorded for a COMPLETED appointment")
    if consultation_repo.get_by_appointment_id(db, appointment_id) is not None:
        raise ConflictError("A consultation has already been recorded for this appointment")

    consultation = consultation_repo.create(
        db,
        appointment_id=appointment_id,
        diagnosis=data.diagnosis,
        prescription=data.prescription,
        notes=data.notes,
        follow_up_date=data.follow_up_date,
    )
    db.commit()

    audit_log("consultation.create", user_id=user.id, consultation_id=consultation.id,
              appointment_id=appointment_id)
    return consultation_repo.get_by_appointment_id(db, appointment_id)


def get_consultation_for_appointment(db: Session, user: User, appointment_id: int) -> Consultation:
    """The patient of the appointment OR its doctor can read the consultation."""
    if user.role == Role.PATIENT.value:
        patient = get_my_patient_profile(db, user)
        appointment = appointment_repo.get_for_patient(db, appointment_id, patient.id)
    elif user.role == Role.DOCTOR.value:
        doctor = get_my_doctor_profile(db, user)
        appointment = appointment_repo.get_for_doctor(db, appointment_id, doctor.id)
    else:
        # Even admins cannot read clinical data.
        raise ForbiddenError("Clinical records are not available for your role")

    # 404 (not 403) when the appointment is somebody else's, so that nobody can
    # find out which appointment ids exist.
    if appointment is None:
        raise NotFoundError("Appointment not found")

    consultation = consultation_repo.get_by_appointment_id(db, appointment_id)
    if consultation is None:
        raise NotFoundError("No consultation has been recorded for this appointment")
    return consultation


def list_my_consultations(db: Session, user: User, doctor_id: Optional[int],
                          from_date: Optional[date], to_date: Optional[date],
                          sort_order: str, page: int, size: int) -> dict:
    patient = get_my_patient_profile(db, user)
    items, total = consultation_repo.list_for_patient(
        db, patient.id, doctor_id, from_date, to_date, sort_order, page, size
    )
    return make_page(items, total, page, size)
