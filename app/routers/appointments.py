"""Appointment endpoints (booking by patients, day view and status by doctors)."""
from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.core.utils import utc_now_naive
from app.db.session import get_db
from app.models.enums import AppointmentStatus, Role
from app.models.user import User
from app.routers.deps import Pagination, get_pagination
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentOut,
    AppointmentReschedule,
    AppointmentStatusUpdate,
)
from app.schemas.common import Page, SortOrder
from app.schemas.consultation import ConsultationCreate, ConsultationOut
from app.services import appointment_service, consultation_service

router = APIRouter(prefix="/appointments", tags=["Appointments"])

patient_only = require_role(Role.PATIENT)
doctor_only = require_role(Role.DOCTOR)


# ---- Patient endpoints -----------------------------------------------------
@router.post("", response_model=AppointmentOut, status_code=201,
             summary="Book a free slot (PATIENT)")
def book_appointment(data: AppointmentCreate, db: Session = Depends(get_db),
                     user: User = Depends(patient_only)):
    return appointment_service.book_appointment(db, user, data)


@router.get("/me", response_model=Page[AppointmentOut],
            summary="My upcoming and past appointments (PATIENT)")
def my_appointments(
    when: Literal["upcoming", "past", "all"] = "all",
    status: Optional[AppointmentStatus] = None,
    sort_by: Literal["date", "booked_at"] = "date",
    sort_order: SortOrder = "asc",
    paging: Pagination = Depends(get_pagination),
    db: Session = Depends(get_db),
    user: User = Depends(patient_only),
):
    return appointment_service.list_my_appointments(
        db, user, when, status.value if status else None, sort_by, sort_order,
        paging.page, paging.size,
    )


# ---- Doctor endpoints ------------------------------------------------------
# NOTE: "/doctor" is declared before the "/{appointment_id}/..." routes.
@router.get("/doctor", response_model=Page[AppointmentOut],
            summary="My appointments for a day (DOCTOR)")
def doctor_appointments(
    slot_date: Optional[date] = Query(None, alias="date", description="Defaults to today (UTC)"),
    status: Optional[AppointmentStatus] = None,
    sort_order: SortOrder = "asc",
    paging: Pagination = Depends(get_pagination),
    db: Session = Depends(get_db),
    user: User = Depends(doctor_only),
):
    day = slot_date or utc_now_naive().date()
    return appointment_service.list_doctor_appointments(
        db, user, day, status.value if status else None, sort_order, paging.page, paging.size
    )


# ---- Actions on one appointment ---------------------------------------------
@router.patch("/{appointment_id}/reschedule", response_model=AppointmentOut,
              summary="Move my appointment to another free slot (PATIENT, own)")
def reschedule(appointment_id: int, data: AppointmentReschedule, db: Session = Depends(get_db),
               user: User = Depends(patient_only)):
    return appointment_service.reschedule_appointment(db, user, appointment_id, data)


@router.patch("/{appointment_id}/cancel", response_model=AppointmentOut,
              summary="Cancel my appointment before the cut-off (PATIENT, own)")
def cancel(appointment_id: int, db: Session = Depends(get_db), user: User = Depends(patient_only)):
    return appointment_service.cancel_appointment(db, user, appointment_id)


@router.patch("/{appointment_id}/status", response_model=AppointmentOut,
              summary="Mark COMPLETED or NO_SHOW (DOCTOR, own)")
def update_status(appointment_id: int, data: AppointmentStatusUpdate, db: Session = Depends(get_db),
                  user: User = Depends(doctor_only)):
    return appointment_service.update_appointment_status(db, user, appointment_id, data)


@router.post("/{appointment_id}/consultation", response_model=ConsultationOut, status_code=201,
             summary="Record diagnosis, prescription and follow-up (DOCTOR, own)")
def record_consultation(appointment_id: int, data: ConsultationCreate, db: Session = Depends(get_db),
                        user: User = Depends(doctor_only)):
    return consultation_service.record_consultation(db, user, appointment_id, data)


@router.get("/{appointment_id}/consultation", response_model=ConsultationOut,
            summary="Read the consultation of one appointment (its PATIENT or DOCTOR only)")
def get_consultation(appointment_id: int, db: Session = Depends(get_db),
                     user: User = Depends(require_role(Role.PATIENT, Role.DOCTOR))):
    return consultation_service.get_consultation_for_appointment(db, user, appointment_id)
