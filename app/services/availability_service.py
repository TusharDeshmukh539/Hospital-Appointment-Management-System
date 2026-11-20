"""Business logic for weekly availability and slots."""
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.core.logging_config import audit_log
from app.core.utils import utc_now_naive
from app.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.availability_template import AvailabilityTemplate
from app.models.slot import Slot
from app.models.enums import SlotStatus
from app.models.user import User
from app.repositories import availability_repo, slot_repo
from app.schemas.availability import AvailabilityCreate, BlockDateRequest, SlotGenerateRequest
from app.services.doctor_service import get_my_doctor_profile


# ----------------------------------------------------------------------------
# Weekly templates
# ----------------------------------------------------------------------------
def add_template(db: Session, user: User, data: AvailabilityCreate) -> AvailabilityTemplate:
    doctor = get_my_doctor_profile(db, user)

    # The window must fit at least one slot.
    window = datetime.combine(date.today(), data.end_time) - datetime.combine(date.today(), data.start_time)
    if window < timedelta(minutes=data.slot_minutes):
        raise BadRequestError("The time window is shorter than one slot")

    # Two templates of the same weekday must not overlap
    # (two time ranges overlap when each starts before the other ends).
    for existing in availability_repo.list_for_weekday(db, doctor.id, data.weekday):
        if data.start_time < existing.end_time and data.end_time > existing.start_time:
            raise ConflictError("This time window overlaps an existing availability on the same weekday")

    template = availability_repo.create(
        db, doctor.id, data.weekday, data.start_time, data.end_time, data.slot_minutes
    )
    db.commit()
    audit_log("availability.create", user_id=user.id, template_id=template.id)
    return template


def list_templates(db: Session, user: User) -> list[AvailabilityTemplate]:
    doctor = get_my_doctor_profile(db, user)
    return availability_repo.list_for_doctor(db, doctor.id)


def delete_template(db: Session, user: User, template_id: int) -> None:
    doctor = get_my_doctor_profile(db, user)
    # Ownership check: the template must belong to THIS doctor.
    template = availability_repo.get_for_doctor(db, template_id, doctor.id)
    if template is None:
        raise NotFoundError("Availability not found")
    availability_repo.delete(db, template)
    db.commit()
    audit_log("availability.delete", user_id=user.id, template_id=template_id)


# ----------------------------------------------------------------------------
# Slot generation
# ----------------------------------------------------------------------------
def generate_slots(db: Session, user: User, data: SlotGenerateRequest) -> dict:
    """Create concrete slots from the weekly templates for every date in the range.

    Business rule 7: never create overlapping slots for the same doctor.
    Slots that already exist (or would overlap one) are skipped, so calling this
    twice for the same range is safe.
    """
    doctor = get_my_doctor_profile(db, user)
    templates = availability_repo.list_for_doctor(db, doctor.id)
    if not templates:
        raise BadRequestError("Define your weekly availability first")

    # Remember the time ranges already used, grouped by date.
    taken: dict[date, list[tuple[time, time]]] = {}
    for slot in slot_repo.list_in_range(db, doctor.id, data.from_date, data.to_date):
        taken.setdefault(slot.slot_date, []).append((slot.start_time, slot.end_time))

    new_slots: list[Slot] = []
    skipped = 0
    current_date = data.from_date
    while current_date <= data.to_date:
        for template in templates:
            if template.weekday != current_date.weekday():  # Monday = 0 ... Sunday = 6
                continue

            # Walk from the window start to the window end, one slot at a time.
            step = timedelta(minutes=template.slot_minutes)
            slot_start = datetime.combine(current_date, template.start_time)
            window_end = datetime.combine(current_date, template.end_time)
            while slot_start + step <= window_end:
                start_time = slot_start.time()
                end_time = (slot_start + step).time()

                overlaps = any(
                    start_time < used_end and end_time > used_start
                    for used_start, used_end in taken.get(current_date, [])
                )
                if overlaps:
                    skipped += 1
                else:
                    new_slots.append(
                        Slot(
                            doctor_id=doctor.id,
                            slot_date=current_date,
                            start_time=start_time,
                            end_time=end_time,
                            status=SlotStatus.FREE.value,
                        )
                    )
                    taken.setdefault(current_date, []).append((start_time, end_time))
                slot_start += step
        current_date += timedelta(days=1)

    slot_repo.add_many(db, new_slots)
    db.commit()
    audit_log("slots.generate", user_id=user.id, created=len(new_slots), skipped=skipped)
    return {"created": len(new_slots), "skipped": skipped}


# ----------------------------------------------------------------------------
# Viewing and blocking slots
# ----------------------------------------------------------------------------
def list_my_slots(db: Session, user: User, slot_date: date) -> list[Slot]:
    """All slots (any status) of the logged-in doctor on one date."""
    doctor = get_my_doctor_profile(db, user)
    return slot_repo.list_for_doctor_on_date(db, doctor.id, slot_date)


def list_free_slots(db: Session, doctor_id: int, slot_date: date) -> list[Slot]:
    """FREE slots of a doctor on one date (what patients see). Past slots are hidden."""
    slots = slot_repo.list_for_doctor_on_date(db, doctor_id, slot_date, SlotStatus.FREE.value)
    now = utc_now_naive()
    return [s for s in slots if datetime.combine(s.slot_date, s.start_time) > now]


def _get_my_slot(db: Session, user: User, slot_id: int) -> Slot:
    """Load a slot and make sure it belongs to the logged-in doctor."""
    doctor = get_my_doctor_profile(db, user)
    slot = slot_repo.get_by_id(db, slot_id)
    if slot is None or slot.doctor_id != doctor.id:
        raise NotFoundError("Slot not found")  # 404 also for other doctors' slots
    return slot


def block_slot(db: Session, user: User, slot_id: int) -> Slot:
    slot = _get_my_slot(db, user, slot_id)
    # Atomic FREE -> BLOCKED. A BOOKED slot cannot be blocked (it has a patient).
    if not slot_repo.block_slot(db, slot.id):
        db.rollback()
        raise ConflictError(f"Only FREE slots can be blocked (this slot is {slot.status})")
    db.commit()
    audit_log("slot.block", user_id=user.id, slot_id=slot_id)
    return slot_repo.get_by_id(db, slot_id)


def unblock_slot(db: Session, user: User, slot_id: int) -> Slot:
    slot = _get_my_slot(db, user, slot_id)
    if not slot_repo.unblock_slot(db, slot.id):
        db.rollback()
        raise ConflictError(f"Only BLOCKED slots can be unblocked (this slot is {slot.status})")
    db.commit()
    audit_log("slot.unblock", user_id=user.id, slot_id=slot_id)
    return slot_repo.get_by_id(db, slot_id)


def block_date(db: Session, user: User, data: BlockDateRequest) -> dict:
    """Block all FREE slots of one date (e.g. the doctor is on leave that day)."""
    doctor = get_my_doctor_profile(db, user)
    blocked = slot_repo.block_free_slots_on_date(db, doctor.id, data.slot_date)
    already_booked = slot_repo.count_with_status_on_date(
        db, doctor.id, data.slot_date, SlotStatus.BOOKED
    )
    db.commit()
    audit_log("slots.block_date", user_id=user.id, blocked=blocked, already_booked=already_booked)
    return {"blocked": blocked, "already_booked": already_booked}
