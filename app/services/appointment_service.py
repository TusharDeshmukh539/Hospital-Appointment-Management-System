"""Business logic for booking, rescheduling, cancelling and completing appointments.

Business rules implemented here (numbers match the case study):
  1. A slot holds at most ONE active appointment; booking a BOOKED/BLOCKED slot -> 409
  2. Slots in the past are not bookable
  3. Cancellation only up to a cut-off (default 2 hours before the slot); slot becomes FREE
  4. Rescheduling is atomic: old slot freed + new slot booked in ONE transaction
  5. A patient may hold at most one active appointment with the same doctor on the same day
"""
from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging_config import audit_log
from app.core.utils import slot_start_datetime, utc_now, utc_now_naive
from app.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.appointment import Appointment
from app.models.availability_template import Slot
from app.models.enums import AppointmentStatus, SlotStatus
from app.models.user import User
from app.repositories import appointment_repo, slot_repo
from app.schemas.appointment import AppointmentCreate, AppointmentReschedule, AppointmentStatusUpdate
from app.schemas.common import make_page
from app.services.doctor_service import get_my_doctor_profile
from app.services.patient_service import get_my_patient_profile


def _check_slot_is_bookable(slot: Optional[Slot]) -> Slot:
    """Checks shared by booking and rescheduling."""
    if slot is None:
        raise NotFoundError("Slot not found")
    if not slot.doctor.user.is_active:
        raise ConflictError("This doctor is not available")
    # Rule 2: no booking in the past
    if slot_start_datetime(slot.slot_date, slot.start_time) <= utc_now_naive():
        raise BadRequestError("Slots in the past cannot be booked")
    # Rule 1 (quick check - the atomic claim below is the real protection)
    if slot.status != SlotStatus.FREE.value:
        raise ConflictError(f"This slot is not available (status: {slot.status})")
    return slot


# ----------------------------------------------------------------------------
# Patient actions
# ----------------------------------------------------------------------------
def book_appointment(db: Session, user: User, data: AppointmentCreate) -> Appointment:
    patient = get_my_patient_profile(db, user)
    slot = _check_slot_is_bookable(slot_repo.get_by_id(db, data.slot_id))

    # Rule 5: only one active appointment per patient + doctor + day
    if appointment_repo.patient_has_active_on_date(db, patient.id, slot.doctor_id, slot.slot_date):
        raise ConflictError("You already have an appointment with this doctor on that day")

    try:
        # Rule 1: atomically change FREE -> BOOKED. If two patients try at the
        # same moment, exactly one gets True here and the other gets False.
        if not slot_repo.claim_slot(db, slot.id):
            raise ConflictError("This slot has just been booked by someone else")

        appointment = appointment_repo.create(
            db, slot_id=slot.id, patient_id=patient.id, doctor_id=slot.doctor_id, reason=data.reason
        )
        db.commit()
    except Exception:
        db.rollback()  # undo everything (including the slot claim) if anything failed
        raise

    audit_log("appointment.book", user_id=user.id, appointment_id=appointment.id, slot_id=data.slot_id)
    return appointment_repo.get_for_patient(db, appointment.id, patient.id)


def reschedule_appointment(db: Session, user: User, appointment_id: int,
                           data: AppointmentReschedule) -> Appointment:
    patient = get_my_patient_profile(db, user)
    # Ownership check: only an appointment of THIS patient is found.
    appointment = appointment_repo.get_for_patient(db, appointment_id, patient.id)
    if appointment is None:
        raise NotFoundError("Appointment not found")
    if appointment.status != AppointmentStatus.BOOKED.value:
        raise ConflictError("Only BOOKED appointments can be rescheduled")
    if data.new_slot_id == appointment.slot_id:
        raise BadRequestError("The new slot is the same as the current slot")

    new_slot = _check_slot_is_bookable(slot_repo.get_by_id(db, data.new_slot_id))
    if new_slot.doctor_id != appointment.doctor_id:
        raise BadRequestError("You can only reschedule to another slot of the same doctor")

    # Rule 5 again for the new date (ignoring the appointment we are moving)
    if appointment_repo.patient_has_active_on_date(
        db, patient.id, new_slot.doctor_id, new_slot.slot_date, exclude_appointment_id=appointment.id
    ):
        raise ConflictError("You already have an appointment with this doctor on that day")

    old_slot_id = appointment.slot_id
    try:
        # Rule 4: all three steps happen in ONE transaction (commit at the end).
        if not slot_repo.claim_slot(db, new_slot.id):  # 1. book the new slot
            raise ConflictError("This slot has just been booked by someone else")
        slot_repo.release_slot(db, old_slot_id)  # 2. free the old slot
        appointment.slot_id = new_slot.id  # 3. point the appointment to the new slot
        db.commit()
    except Exception:
        db.rollback()  # nothing is half-done: both slots stay as they were
        raise

    audit_log(
        "appointment.reschedule", user_id=user.id, appointment_id=appointment_id,
        old_slot_id=old_slot_id, new_slot_id=new_slot.id,
    )
    return appointment_repo.get_for_patient(db, appointment_id, patient.id)


def cancel_appointment(db: Session, user: User, appointment_id: int) -> Appointment:
    patient = get_my_patient_profile(db, user)
    appointment = appointment_repo.get_for_patient(db, appointment_id, patient.id)
    if appointment is None:
        raise NotFoundError("Appointment not found")
    if appointment.status != AppointmentStatus.BOOKED.value:
        raise ConflictError("Only BOOKED appointments can be cancelled")

    # Rule 3: cancellation is only allowed up to the cut-off time before the slot.
    cutoff_hours = get_settings().CANCELLATION_CUTOFF_HOURS
    slot_start = slot_start_datetime(appointment.slot.slot_date, appointment.slot.start_time)
    if utc_now_naive() > slot_start - timedelta(hours=cutoff_hours):
        raise BadRequestError(
            f"Appointments can only be cancelled at least {cutoff_hours} hours before the slot"
        )

    try:
        appointment.status = AppointmentStatus.CANCELLED.value
        appointment.cancelled_at = utc_now()
        slot_repo.release_slot(db, appointment.slot_id)  # slot returns to FREE
        db.commit()
    except Exception:
        db.rollback()
        raise

    audit_log("appointment.cancel", user_id=user.id, appointment_id=appointment_id)
    return appointment_repo.get_for_patient(db, appointment_id, patient.id)


def list_my_appointments(db: Session, user: User, when: str, status: Optional[str],
                         sort_by: str, sort_order: str, page: int, size: int) -> dict:
    patient = get_my_patient_profile(db, user)
    items, total = appointment_repo.list_for_patient(
        db, patient.id, when, status, sort_by, sort_order, page, size
    )
    return make_page(items, total, page, size)


# ----------------------------------------------------------------------------
# Doctor actions
# ----------------------------------------------------------------------------
def list_doctor_appointments(db: Session, user: User, slot_date, status: Optional[str],
                             sort_order: str, page: int, size: int) -> dict:
    doctor = get_my_doctor_profile(db, user)
    items, total = appointment_repo.list_for_doctor_on_date(
        db, doctor.id, slot_date, status, sort_order, page, size
    )
    return make_page(items, total, page, size)


def update_appointment_status(db: Session, user: User, appointment_id: int,
                              data: AppointmentStatusUpdate) -> Appointment:
    """The assigned doctor marks an appointment COMPLETED or NO_SHOW."""
    doctor = get_my_doctor_profile(db, user)
    appointment = appointment_repo.get_for_doctor(db, appointment_id, doctor.id)
    if appointment is None:
        raise NotFoundError("Appointment not found")
    if appointment.status != AppointmentStatus.BOOKED.value:
        raise ConflictError(f"Appointment is already {appointment.status}")

    # The slot stays BOOKED on purpose: the visit happened (or was missed),
    # so nobody else may take this time again.
    appointment.status = data.status
    db.commit()

    audit_log("appointment.status", user_id=user.id, appointment_id=appointment_id, status=data.status)
    return appointment_repo.get_for_doctor(db, appointment_id, doctor.id)
